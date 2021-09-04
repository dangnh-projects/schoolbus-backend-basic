from django.contrib.auth.models import User
from django.db import transaction
from django.utils.translation import gettext as _
from django.utils import timezone
from rest_framework.exceptions import NotFound
from datetime import datetime, timedelta
from math import floor
from fcm_django.models import FCMDevice
from rest_framework.utils import json

from .models import Bus, Parent, BusSupervisor, Driver, BusRoute, BusLocation, \
    Student, BusLocationWithStudents, BusRouteWithLocation, Attendance, BusRouteHistory, \
    NotificationLog, NotificationTemplate, Contact
from settings.models import SystemConfiguration
from django.conf import settings
from .serializers import StudentSerializer, DriverSerializer, BusSupervisorSerializer, \
    BusSerializer, BusLocationSerializer, ContactSerializer
from .constants import *

from infra.utils import send_to_fb_topic, convert_str_to_date


def set_absence_for_student(location, student, from_date, to_date, message,
                            by_parent):
    running_date = convert_str_to_date(from_date)
    to_date = convert_str_to_date(to_date)
    student_with_locations = BusLocationWithStudents.objects.filter(
        student=student, bus_location__in=location)

    attendances = []
    while running_date <= to_date:
        for student_with_location in student_with_locations:
            f = {
                'bus_location_with_student': student_with_location,
                'current_date': running_date.date()
            }
            old_attendances = Attendance.objects.filter(**f)
            for attendance in old_attendances:
                attendance.delete()
            f['status'] = STUDENT_STATUS[2][0]
            f['reason_for_absence_or_missing'] = message
            f['report_absence_by_parent'] = by_parent
            attendances.append(Attendance(**f))

        running_date = running_date + timedelta(days=1)
    Attendance.objects.bulk_create(attendances)


def save_parent_locale(parent, locale):
    parent.preferred_langage = locale
    parent.save()


def query_students_and_routes_for_parent(parent):
    students = Student.objects.filter(parent=parent)
    result = []
    for student in students:
        routes = query_route_list_of_student(student)
        result.append({'student_id': student.pk, 'routes': routes})
    return result


def query_route_list_of_student(student):
    student_with_locations = BusLocationWithStudents.objects.filter(
        student=student)

    result = []
    for student_with_location in student_with_locations:
        route_with_locations = BusRouteWithLocation.objects.filter(
            bus_location=student_with_location.bus_location)
        for route_with_location in route_with_locations:
            bus_route = route_with_location.bus_route
            result.append(bus_route.pk)

    return result


def query_routes_of_student(student_id):
    student_with_locations = BusLocationWithStudents.objects.filter(
        student=student_id)

    result = {}
    for student_with_location in student_with_locations:
        route_with_locations = BusRouteWithLocation.objects.filter(
            bus_location=student_with_location.bus_location)
        for route_with_location in route_with_locations:
            bus_route = route_with_location.bus_route
            if bus_route.route_type not in result:
                result[bus_route.route_type] = []
            result[bus_route.route_type].append(
                BusLocationSerializer(student_with_location.bus_location).data)
    return result


def update_student_status_of_route(raw_data, route_id):
    route_with_locations = BusRouteWithLocation.objects.filter(
        bus_route=route_id)
    result = []
    locations = [
        route_with_location.bus_location
        for route_with_location in route_with_locations
    ]

    for data in raw_data:
        bus_location_with_student = BusLocationWithStudents.objects.filter(
            student=data['pk'], bus_location__in=locations).first()
        attendance = Attendance.objects.filter(
            bus_location_with_student=bus_location_with_student.pk,
            current_date=datetime.now().date()).first()
        attendance.status = data['status_code']
        attendance.reason_for_absence_or_missing = data[
            'message'] if 'message' in data else None

        if attendance.report_absence_by_parent == True:
            if data['status_code'] != STUDENT_STATUS[2][0]:
                attendance.report_absence_by_parent = False

        attendance.save()
        result.append([bus_location_with_student.student, attendance])

    return result


def update_student_status_at_location(raw_data, location_id):
    result = []
    for data in raw_data:
        bus_location_with_student = BusLocationWithStudents.objects.filter(
            student=data['pk'], bus_location=location_id).first()
        attendance = Attendance.objects.filter(
            bus_location_with_student=bus_location_with_student.pk,
            current_date=datetime.now().date()).first()
        attendance.status = data['status_code']

        if attendance.report_absence_by_parent:
            if data['status_code'] != STUDENT_STATUS[2][0]:
                attendance.report_absence_by_parent = False

        attendance.save()
        result.append([bus_location_with_student.student, attendance])

    return result


def update_location_to_passed(student_ids=[], route_id=None):
    location_with_students = BusLocationWithStudents.objects.filter(
        student__in=student_ids)
    BusRouteWithLocation.objects.filter(
        bus_route=route_id,
        bus_location__in=[
            location_with_student.bus_location
            for location_with_student in location_with_students
        ]).update(status=1)


@transaction.atomic
def set_missing_for_student(raw_data, location_id):
    # ra_data = { 1: 'message 1', 2: 'message 2'}
    bus_locations = BusLocationWithStudents.objects.filter(
        student__in=(*raw_data, ), bus_location=location_id)

    for bus_location in bus_locations:
        attendance = Attendance.objects.filter(
            bus_location_with_student=bus_location,
            current_date=datetime.now().date()).first()

        if attendance:
            attendance.status = STUDENT_STATUS[1][0]
            attendance.reason_for_absence_or_missing = raw_data[
                "%s" % bus_location.student.pk]
            attendance.save()


def query_next_stop_students(location_id):
    bus_location_with_students = BusLocationWithStudents.objects.filter(
        bus_location=location_id)
    result = []
    for bus_location_with_student in bus_location_with_students:
        student = bus_location_with_student.student
        bus_location = bus_location_with_student.bus_location

        parent = student.parent
        parent_info = parent.info

        attendances = Attendance.objects.filter(
            bus_location_with_student=bus_location_with_student,
            current_date=datetime.now().date())

        if len(attendances) > 1:
            print(
                'THIS IS WRONG..................... ATTENDANCE SHOULD ONLY HAS ONE'
            )

        status = resolve_status(attendances[0].status)
        result.append({
            'location_id': bus_location.pk,
            'id': student.pk,
            'name': student.name,
            'image': student.image.url,
            'status_code': attendances[0].status,
            'status': status,
            'class': student.classroom,
            'age': compute_age(student.dob),
            'parent': {
                'id': parent_info.pk,
                'name':
                "%s %s" % (parent_info.first_name, parent_info.last_name),
                'phone': parent.phone_number
            },
        })

    return result


def query_journey(route_id):
    content = {
        'journey': {
            'route_id': route_id,
        }
    }

    route = BusRoute.objects.get(pk=route_id)
    bus_route_with_locations = BusRouteWithLocation.objects.filter(
        bus_route=route.pk).order_by('order')
    locations = []
    for bus_route_with_location in bus_route_with_locations:
        location = bus_route_with_location.bus_location
        locations.append({
            'id': location.pk,
            'address': location.address,
            'street': location.street,
            'ward': location.ward,
            'district': location.district,
            'long': location.lng,
            'lat': location.lat
        })

        content['journey']['locations'] = locations
    return content


def query_bus_info_for_supervisor(supervisor_id=None):
    routes = BusRoute.objects.filter(bus_supervisor=supervisor_id)

    content = {}
    for route in routes:
        bus = route.bus
        supervisor = route.bus_supervisor
        driver = route.driver

        bus_route_with_locations = BusRouteWithLocation.objects.filter(
            bus_route=route.pk)

        location_ids = [
            bus_route_with_location.bus_location
            for bus_route_with_location in bus_route_with_locations
        ]

        bus_location_with_students = BusLocationWithStudents.objects.filter(
            bus_location__in=location_ids).distinct()
        absences = Attendance.objects.filter(
            status=STUDENT_STATUS[2][0],
            current_date=datetime.now().date(),
            bus_location_with_student__in=bus_location_with_students).distinct(
            )

        data = {
            'route_id': route.pk,
            'bus': {
                'id': bus.pk,
                'name': bus.name,
                'vehicle_registration_plate': bus.vehicle_registration_plate,
            },
            'driver': {
                'id': driver.pk,
                'name': driver.name,
                'image':
                driver.image.url if driver.image is not None else None,
                'phone': driver.phone
            },
            'students': {
                'number': len(bus_location_with_students),
                'absence_today': len(absences)
            }
        }
        key = "%s" % route.route_type
        current = content.get(key, [])
        current.append(data)
        content[key] = current

    return content


def reset_attendance_status(attendances):
    new_attendances = []
    checked_bus_location_with_student_ids = []
    for attendance in attendances:
        status = STUDENT_STATUS[0][0]  #
        # reset status to "not on bus yet" except the one absence reported by parent
        if attendance.status == STUDENT_STATUS[2][
                0] and attendance.report_absence_by_parent == True:
            status = STUDENT_STATUS[2][0]

        new_attendance = Attendance(
            bus_location_with_student=attendance.bus_location_with_student,
            current_date=attendance.current_date,
            reason_for_absence_or_missing=attendance.
            reason_for_absence_or_missing,
            report_absence_by_parent=attendance.report_absence_by_parent,
            status=status)
        checked_bus_location_with_student_ids.append(
            attendance.bus_location_with_student.pk)
        new_attendances.append(new_attendance)
        attendance.delete()

    return new_attendances, checked_bus_location_with_student_ids


def init_attendance(bus_route_id):
    # if start this route again, all the attendance should be reprocessed
    attendances, locations = query_attendances_and_location_of_bus_route(
        bus_route_id)

    # reset all the absence attendances except the one reported by parent
    new_attendances, checked_bus_location_with_student_ids = reset_attendance_status(
        attendances)

    # create the new attendance records for current date
    location_with_students = BusLocationWithStudents.objects.filter(
        bus_location__in=locations).exclude(
            pk__in=checked_bus_location_with_student_ids)
    for location_with_student in location_with_students:
        new_attendance = Attendance(
            bus_location_with_student=location_with_student,
            current_date=datetime.now().date(),
            status=STUDENT_STATUS[0][0])
        new_attendances.append(new_attendance)

    Attendance.objects.bulk_create(new_attendances)


@transaction.atomic
def end_journey(route_id):
    route = BusRoute.objects.get(pk=route_id)
    route.is_running = False
    route.end_time = timezone.now()
    BusRouteWithLocation.objects.filter(bus_route=route).update(status=0,
                                                                delay_time="0")
    BusRouteHistory.objects.create(bus_route=route, status=0)
    route.save()


def notify_start_journey(route_id, journey_type):
    result = send_to_fb_topic(
        topic='route_%s' % route_id,
        data_message={'type': 'start_%s' % (journey_type)})
    return result


def init_bus_location(route):
    BusRouteWithLocation.objects.filter(bus_route=route).update(status=0,
                                                                delay_time="0")


@transaction.atomic
def start_journey(user, journey_type):
    supervisor = BusSupervisor.objects.get(info=user.pk)
    route_type = ROUTE_TYPE._filter_from_url(journey_type)
    route = BusRoute.objects.filter(bus_supervisor=supervisor.pk,
                                    route_type=route_type[0]).first()
    if route:
        route.is_running = True
        route.start_time = timezone.now()
        route.save()
        BusRouteHistory.objects.create(bus_route=route, status=1)
        init_attendance(route.pk)
        init_bus_location(route)
        return route.pk
    return None


def query_student_estimation_for_parent(student_id, route_id):
    student = Student.objects.filter(pk=student_id).first()
    student_info = query_student_and_bus_info(student)

    route_with_locations = BusRouteWithLocation.objects.filter(
        order__lte=student_info['location']['order'],
        status=0,
        bus_route__pk=route_id)

    estimated_time = 0

    if route_with_locations is None or len(route_with_locations) == 0:
        student_info['estimated_time'] = 0
        return student_info

    for route_with_location in route_with_locations:
        estimated_time += route_with_location.estimated_travelling_time

    current_bus_route_with_location = list(route_with_locations)[-1]
    sum_delay_time = sum(
        int(t) for t in current_bus_route_with_location.delay_time.split(";"))

    student_info['estimated_time'] = estimated_time + sum_delay_time

    return student_info


def compute_age(dob):
    age = datetime.now().date() - dob
    return floor(age.days / 365.2425)


def resolve_status(status):
    return list(filter(lambda s: status == s[0], STUDENT_STATUS))[0][1]


def query_info_for_active_route(active_route_with_location, student,
                                student_info):
    bus_location = active_route_with_location.bus_location
    bus_location_order = active_route_with_location.order
    location_with_students = BusLocationWithStudents.objects.filter(
        bus_location=bus_location, student=student)
    bus_route = active_route_with_location.bus_route
    bus = bus_route.bus
    route_type = bus_route.route_type
    supervisor = bus_route.bus_supervisor
    attendance = Attendance.objects.filter(
        bus_location_with_student__in=location_with_students,
        current_date=timezone.now().date()).order_by('-created_on').first()

    bus_status = 0 if route_type == 'P' else 2
    student_info['bus'] = {
        'start_time': int(bus_route.start_time.timestamp() * 1000),
        'status_code': BUS_STATUS[bus_status][0],
        'status': BUS_STATUS[bus_status][1]
    }

    return bus, bus_route, bus_location, supervisor, attendance, student_info, bus_location_order


def query_student_and_bus_info(student):
    school = student.school
    student_info = {
        'id': student.pk,
        'name': student.name,
        'image': student.image.url,
        'class': student.classroom,
        'age': compute_age(student.dob),
        'school': school.name,
        'school_logo': school.logo.url
    }

    locations_with_student = BusLocationWithStudents.objects.filter(
        student=student.pk)
    locations = []
    for location_with_student in locations_with_student:
        locations.append(location_with_student.bus_location)

    active_route_with_location = BusRouteWithLocation.objects.filter(
        bus_location__in=locations, bus_route__is_running=True).first()

    bus = Bus()
    bus_route = BusRoute()
    supervisor = BusSupervisor()
    bus_location = BusLocation()
    attendance = None
    bus_location_order = 0

    if active_route_with_location:
        bus, bus_route, bus_location, supervisor, attendance, student_info, bus_location_order = query_info_for_active_route(
            active_route_with_location, student, student_info)
    else:
        location_with_student = BusLocationWithStudents.objects.filter(
            bus_location__in=locations,
            student=student).order_by('-updated_on')
        attendance = Attendance.objects.filter(
            bus_location_with_student__in=location_with_student,
            current_date=timezone.now().date()).order_by(
                '-created_on').first()
        student_info['bus'] = {
            'start_time': None,
            'status_code': BUS_STATUS[1][0],
            'status': BUS_STATUS[1][1]
        }

    student_info['bus']['name'] = bus.name
    student_info['bus'][
        'vehicle_registration_plate'] = bus.vehicle_registration_plate
    student_info['bus'][
        'estimated_start_time'] = bus_route.estimated_start_time
    student_info['route_id'] = bus_route.pk
    student_info['supervisor'] = {'phone': supervisor.phone_number}
    if attendance is None:
        student_info['status_code'] = STUDENT_STATUS[0][0]
        student_info['status'] = STUDENT_STATUS[0][1]
        student_info['report_absence_by_parent'] = False
    else:
        student_info['status_code'] = attendance.status
        student_info['status'] = resolve_status(attendance.status)
        student_info[
            'report_absence_by_parent'] = attendance.report_absence_by_parent

    student_info['location'] = {
        **BusLocationSerializer(bus_location).data, 'order': bus_location_order
    }
    return student_info


def query_students_for_parent(user):
    students = Student.objects.filter(parent=user.id)
    result = []

    for student in students:
        student_info = query_student_and_bus_info(student)
        result.append(student_info)

    return result


@transaction.atomic
def create_supervisor(request):
    username = request.POST["username"]
    password = request.POST["password"]
    first_name = request.POST["first_name"]
    last_name = request.POST["last_name"]
    email = request.POST["email"]
    # create user for bus supervisor
    body_data = request.POST
    data = body_data.dict()
    for key in ["username", "password", 'first_name', 'last_name', 'email']:
        del data[key]

    avatar = request.FILES.get("avatar", None)
    if avatar:
        data["avatar"] = avatar

    user = User.objects.create_user(
        username,
        email,
        password,
        is_staff=True,
        first_name=first_name,
        last_name=last_name,
    )
    data["info"] = user

    supervisor = BusSupervisor.objects.create(**data)
    return supervisor


@transaction.atomic
def update_supervisor(request, pk):
    body_data = request.POST
    first_name = request.POST["first_name"]
    last_name = request.POST["last_name"]
    email = request.POST["email"]
    supervisor = BusSupervisor.objects.filter(id=pk).first()
    password = request.POST.get("password", None)

    if not supervisor:
        raise NotFound(detail=_('Bus supervisor not exists'))

    data = body_data.dict()
    supervisor.info.__dict__.update(first_name=first_name,
                                    last_name=last_name,
                                    email=email)

    if password:
        supervisor.info.set_password(password)

    avatar = request.FILES.get("avatar", False)
    if avatar:
        data["avatar"] = avatar

    supervisor.__dict__.update(**data)
    supervisor.save()
    supervisor.info.save()

    return supervisor


@transaction.atomic
def create_parent(request):
    username = request.POST["username"]
    password = request.POST["password"]
    first_name = request.POST["first_name"]
    last_name = request.POST["last_name"]
    email = request.POST["email"]

    # save bus supervisor
    body_data = request.POST
    data = body_data.dict()

    avatar = request.FILES.get("avatar", None)
    if avatar:
        data["avatar"] = avatar

    for key in ["username", "password", "first_name", "last_name", "email"]:
        del data[key]

    # create user for  Parent
    user = User.objects.create_user(username=username,
                                    password=password,
                                    first_name=first_name,
                                    last_name=last_name,
                                    email=email)
    data["info"] = user
    parent = Parent.objects.create(**data)
    return parent


@transaction.atomic
def update_parent(request, pk):
    parent = Parent.objects.filter(info=pk).first()
    if not parent:
        raise NotFound(detail=_('Parent not exists'))

    first_name = request.POST["first_name"]
    last_name = request.POST["last_name"]
    email = request.POST["email"]
    password = request.POST["password"]

    body_data = request.POST
    data = body_data.dict()

    for key in ["username", "password", "first_name", "last_name", "email"]:
        del data[key]

    avatar = request.FILES.get("avatar", False)
    if avatar:
        data["avatar"] = avatar

    parent.__dict__.update(**data)
    parent.save()

    if password:
        parent.info.set_password(password)

    if first_name:
        parent.info.__dict__.update(first_name=first_name)

    if last_name:
        parent.info.__dict__.update(last_name=last_name)

    if email:
        parent.info.__dict__.update(email=email)

    parent.info.save()
    return parent


@transaction.atomic
def create_contact(request):
    request.POST._mutable = True

    body_data = request.POST

    parent_id = request.POST['parent']
    parent = Parent.objects.get(pk=parent_id)
    body_data['parent'] = parent

    data = body_data.dict()

    contact = Contact.objects.create(**data)
    return contact


@transaction.atomic
def update_contact(request, pk):
    body_data = request.POST
    contact = Contact.objects.get(id=pk)

    if not contact:
        raise NotFound(detail=_('Contact not exists'))

    data = body_data.dict()

    contact.__dict__.update(**data)
    contact.save()

    return contact


@transaction.atomic
def create_student(request):
    body_data = request.POST
    data = body_data.dict()

    image = request.FILES.get("image", None)
    if image:
        data["image"] = image

    student = Student.objects.create(**data)
    return student


@transaction.atomic
def update_student(request, pk):
    body_data = request.POST
    student = Student.objects.filter(id=pk).first()

    if not student:
        raise NotFound(detail=_('Student not exists'))

    data = body_data.dict()
    image = request.FILES.get("image", False)
    if image:
        data["image"] = image
    if data.get("parent_id") and int(data["parent_id"]) == -1:
        data["parent_id"] = None

    student.__dict__.update(**data)
    student.save()

    return student


@transaction.atomic
def create_driver(request):
    # save bus supervisor
    body_data = request.POST
    print(body_data)
    data = body_data.dict()

    image = request.FILES.get("image", None)

    if image:
        data["image"] = image
    driver = Driver.objects.create(**data)
    return driver


@transaction.atomic
def update_driver(request, pk):
    body_data = request.POST
    driver = Driver.objects.filter(id=pk).first()

    if not driver:
        raise NotFound(detail=_('Driver not exists'))

    data = body_data.dict()
    image = request.FILES.get("image", False)
    if image:
        data["image"] = image

    driver.__dict__.update(**data)
    driver.save()

    return driver


@transaction.atomic
def save_bus_route(request):
    body_data = request.POST

    name = body_data.get("name")
    route_type = body_data.get("route_type")
    estimated_start_time = body_data.get("estimated_start_time")
    estimated_end_time = body_data.get("estimated_end_time")

    bus = Bus.objects.filter(id=body_data.get("bus", None)).first()
    if not bus:
        raise NotFound(detail="Bus not found")

    bus_supervisor = BusSupervisor.objects.filter(
        id=body_data.get("bus_supervisor", None)).first()
    if not bus_supervisor:
        raise NotFound(detail="Bus supervisor not found")

    driver = Driver.objects.filter(id=body_data.get("driver", None)).first()
    if not driver:
        raise NotFound(detail="Driver not found")

    bus_route = BusRoute.objects.create(
        name=name,
        route_type=route_type,
        bus=bus,
        bus_supervisor=bus_supervisor,
        driver=driver,
        estimated_start_time=estimated_start_time,
        estimated_end_time=estimated_end_time)

    # bus_route = BusRoute.objects.create(**body_data)
    return bus_route


@transaction.atomic
def save_bus_location(request):
    body = request.POST

    route = body.get("route", None)
    data = body.dict()
    order = body.get("order", 0)
    estimated_travelling_time = body.get("estimated_travelling_time", 0)

    for key in [
            "route", "previous_location", "order", "estimated_travelling_time"
    ]:
        if data.get(key):
            del data[key]

    address = body.get("address", "")
    street = body.get("street", "")
    ward = body.get("ward", "")
    district = body.get("district", "")
    lat = body.get("lat", "")
    lng = body.get("lng", "")

    new_location = BusLocation.objects.create(**data)

    if route:
        # First stop of route
        current_route = BusRoute.objects.filter(id=route).first()

        BusRouteWithLocation.objects.create(
            bus_route=current_route,
            bus_location=new_location,
            order=order,
            estimated_travelling_time=estimated_travelling_time)

        return new_location


@transaction.atomic
def update_bus_location(request, pk):
    body_data = request.POST
    bus_location = BusLocation.objects.filter(id=pk).first()

    estimated_travelling_time = body_data.get("estimated_travelling_time", 0)

    if not bus_location:
        raise NotFound(detail=_('bus_location not exists'))

    data = body_data.dict()

    for key in ["estimated_travelling_time"]:
        if data.get(key):
            del data[key]

    bus_location.__dict__.update(**data)
    bus_location.save()

    BusRouteWithLocation.objects.filter(
        bus_location=bus_location, bus_route=body_data["route"]).update(
            estimated_travelling_time=estimated_travelling_time)

    return bus_location


def get_route_locations(route_id):
    route = BusRoute.objects.filter(id=route_id).first()

    if not route:
        raise NotFound(detail="Route not found")
        return

    locations = []
    # location = BusLocation.objects.filter(id=route.first_location.id).first()
    # while (location):
    #     locations.append(location)
    #     if not location.next_location:
    #         break
    #     location = BusLocation.objects.filter(
    #         id=location.next_location.id).first()

    locations = BusRouteWithLocation.objects.filter(bus_route=route)
    return locations


def get_parent_by_id_number(id_number):
    parent = Parent.objects.filter(id_number=id_number).first()

    if not parent:
        raise NotFound(detail="Parent not found")

    students = Student.objects.filter(parent=parent)

    return parent, students


def get_bus_route_by_type(route_type):
    routes = BusRoute.objects.filter(route_type=route_type)

    return routes


def assign_student_to_route(route, location, student):
    bus_route = BusRoute.objects.filter(id=route).first()

    if not bus_route:
        raise NotFound(detail="Route not found")

    route_type = bus_route.route_type

    student = Student.objects.filter(id=student).first()
    if not student:
        raise NotFound(detail="Student not found")

    selected_location = BusLocation.objects.filter(id=location).first()
    if not selected_location:
        raise NotFound(detail="Location not found")

    bus_location_with_students = BusLocationWithStudents.objects.filter(
        student=student)

    bus_locations = [item.bus_location for item in bus_location_with_students]

    current_bus_route_with_location = BusRouteWithLocation.objects.filter(
        bus_location__in=bus_locations,
        bus_route__route_type=route_type).first()

    if current_bus_route_with_location:
        current_location_with_student = BusLocationWithStudents.objects.filter(
            student=student,
            bus_location=current_bus_route_with_location.bus_location).first()

        if current_bus_route_with_location.bus_location != selected_location:
            current_location_with_student.delete()
        else:
            return current_location_with_student

    new_student_location = BusLocationWithStudents.objects.create(
        student=student, bus_location_id=location)

    return new_student_location


def notification_logging(f):
    def logging(*args, **kwargs):
        data = list(args)[0]
        bus_route = BusRoute.objects.get(pk=data['route_id'])
        sender = "System" if data.get('supervisor') == None else "%s %s" % (
            data['supervisor'].first_name, data['supervisor'].last_name)
        route_type = "Drop off" if bus_route.route_type == "D" else "Pick up"
        receiver = "%s %s" % (data['parent'].first_name,
                              data['parent'].last_name)

        NotificationLog.objects.create(route_type=route_type,
                                       route_name=bus_route.name,
                                       sender=sender,
                                       receiver=receiver,
                                       student=data['student_id'],
                                       content=data['body'])
        return f(*args, **kwargs)

    return logging


@notification_logging
def send_notification_to_parents(data):
    devices = FCMDevice.objects.filter(user=data['parent'].pk, active=True)
    for device in devices:
        device.send_message(title=data['title'], body=data['body'])


@transaction.atomic
def set_student_onbus(student_ids, location_id):
    bus_location_with_students = BusLocationWithStudents.objects.filter(
        bus_location=location_id, student__in=student_ids)
    attendances = Attendance.objects.filter(
        bus_location_with_student__in=bus_location_with_students)

    for attendance in attendances:
        attendance.status = STUDENT_STATUS[3][0]
        attendance.reason_for_absence_or_missing = None
        attendance.save()

    return True


def query_students_from_route(route_id):
    bus_route_with_locations = BusRouteWithLocation.objects.filter(
        bus_route=route_id)
    bus_location_ids = [
        bus_route_with_location.bus_location.pk
        for bus_route_with_location in bus_route_with_locations
    ]
    location_with_students = BusLocationWithStudents.objects.filter(
        bus_location__in=bus_location_ids)

    data = []
    for location_with_student in location_with_students:
        student = location_with_student.student
        parent = student.parent
        attendance = Attendance.objects.get(
            bus_location_with_student=location_with_student,
            current_date=datetime.now().date())
        info = {
            'id': student.pk,
            'name': student.name,
            'class': student.classroom,
            'image': student.image.url,
            'parent': {
                'phone': parent.phone_number
            },
            'report_absence_by_parent': False,
        }
        status = None
        status_code = None

        if attendance:
            info['status_code'] = attendance.status
            info['status'] = resolve_status(attendance.status)
            info[
                'report_absence_by_parent'] = attendance.report_absence_by_parent

        data.append(info)
    return data


def query_attendances_and_location_of_bus_route(route):
    bus_route = BusRoute.objects.filter(id=route).first()

    if not bus_route:
        raise NotFound(detail="Route not found")

    bus_locations = [
        item.bus_location
        for item in BusRouteWithLocation.objects.filter(bus_route=bus_route)
    ]

    bus_location_with_students = BusLocationWithStudents.objects.filter(
        bus_location__in=bus_locations)

    attendances = Attendance.objects.filter(
        bus_location_with_student__in=bus_location_with_students)

    return attendances, bus_locations


def query_moving_routes():
    moving_bus_routes = BusRoute.objects.filter(is_running=True)

    bus_route_data = []

    for bus_route in moving_bus_routes:

        locations = BusRouteWithLocation.objects.filter(bus_route=bus_route)
        location_data = []
        for location in locations:
            location_with_students = BusLocationWithStudents.objects.filter(
                bus_location=location.bus_location)

            attendances = Attendance.objects.filter(
                bus_location_with_student__in=location_with_students,
                current_date=datetime.now().date())
            info = {
                "location":
                BusLocationSerializer(location.bus_location).data,
                "order":
                location.order,
                "attendances": [{
                    "student":
                    StudentSerializer(
                        item.bus_location_with_student.student).data,
                    "status":
                    item.status
                } for item in attendances]
            }

            location_data.append(info)

        bus_route_item = {
            "bus_route": {
                "id":
                bus_route.id,
                "name":
                bus_route.name,
                "start_time":
                bus_route.start_time,
                "estimated_end_time":
                bus_route.estimated_end_time,
                "bus_supervisor":
                BusSupervisorSerializer(bus_route.bus_supervisor).data,
                "driver":
                DriverSerializer(bus_route.driver).data,
                "bus":
                BusSerializer(bus_route.bus).data,
                "route_type":
                bus_route.route_type
            },
            "locations": location_data
        }

        bus_route_data.append(bus_route_item)

    return bus_route_data


@transaction.atomic
def update_delay_time(minutes, route_id):
    route_with_locations = BusRouteWithLocation.objects.filter(
        bus_route=route_id, status=0)
    result = []
    for route_with_location in route_with_locations:
        current = route_with_location.delay_time
        route_with_location.delay_time = "%s;%s" % (current, minutes)
        route_with_location.save()
        result.append({
            'id': route_with_location.bus_location.pk,
            'delay_time': route_with_location.delay_time
        })

    topic = "route_%s" % (route_id, )
    notification_result = send_to_fb_topic(topic=topic,
                                           data_message={'type': 'delay'})

    return result


def get_routes_by_bus(bus_id):
    bus = Bus.objects.filter(id=bus_id).first()
    if not bus:
        raise NotFound(detail="Bus not found")

    routes = BusRoute.objects.filter(bus=bus)

    return routes


def get_routes_by_driver(driver_id):
    driver = Driver.objects.filter(id=driver_id).first()
    if not driver:
        raise NotFound(detail="Driver not found")

    routes = BusRoute.objects.filter(driver=driver)

    return routes


def get_routes_by_bus_supervisor(bus_supervisor_id):
    bus_supervisor = BusSupervisor.objects.filter(id=bus_supervisor_id).first()
    if not bus_supervisor:
        raise NotFound(detail="Bus supervisor not found")

    routes = BusRoute.objects.filter(bus_supervisor=bus_supervisor)

    return routes


def update_bus_route_with_location(request, pk):
    body_data = request.POST
    bus_route_with_location = BusRouteWithLocation.objects.filter(
        id=pk).first()

    if not bus_route_with_location:
        raise NotFound(detail=_('bus_location not exists'))

    data = body_data.dict()

    bus_route_with_location.__dict__.update(**data)
    bus_route_with_location.save()

    return bus_route_with_location


def create_or_update_notification_template(data):
    result = []
    for key, value in data.items():
        notif_template, created = NotificationTemplate.objects.get_or_create(
            notification_type=int(key))
        notif_template.vn_text = value['vn_text']
        notif_template.en_text = value['en_text']
        notif_template.save()
        result.append(notif_template)

    return result


def get_notification_template():
    templates = NotificationTemplate.objects.all()
    result = {}
    for template in templates:
        result[template.notification_type] = {
            'en_text': template.en_text,
            'vn_text': template.vn_text
        }

    return result


def remove_student_with_location(location, student):
    student = Student.objects.filter(id=student).first()
    if not student:
        raise NotFound(detail="Student not found")

    selected_location = BusLocation.objects.filter(id=location).first()

    BusLocationWithStudents.objects.filter(
        student=student, bus_location=selected_location).delete()


def query_route_info_by_student(student, route_type):
    locations_with_student = BusLocationWithStudents.objects.filter(
        student__id=student)

    route_with_locations = BusRouteWithLocation.objects.filter(
        bus_location__in=[
            location_with_student.bus_location
            for location_with_student in locations_with_student
        ],
        bus_route__route_type=route_type)

    if route_with_locations is not None and len(route_with_locations) > 0:
        bus_route = route_with_locations[0].bus_route
        bus_locations = [
            route_with_location.bus_location
            for route_with_location in route_with_locations
        ]
        driver = bus_route.driver
        bus = bus_route.bus
        bus_supervisor = bus_route.bus_supervisor
        bus_supervisor_user = bus_supervisor.info
        current_route_with_locations = BusRouteWithLocation.objects.filter(
            bus_route=bus_route)

        locations = []
        for current_route_with_location in current_route_with_locations:
            location = current_route_with_location.bus_location
            locations.append({
                'address':
                location.address,
                'street':
                location.street,
                'ward':
                location.ward,
                'district':
                location.district,
                'province':
                location.province,
                'owned':
                True if location.pk == bus_locations[0].pk else False
            })

        return {
            'bus': {
                'name': bus.name,
                'vehicle_registration_plate': bus.vehicle_registration_plate
            },
            'driver': {
                'name': driver.name,
                'phone': driver.phone,
                'avatar': driver.image.url
            },
            'supervisor': {
                'name':
                "%s %s" % (bus_supervisor_user.first_name,
                           bus_supervisor_user.last_name),
                'phone':
                bus_supervisor.phone_number,
                'avatar':
                bus_supervisor.avatar.url
            },
            'locations': locations
        }

    return None


def query_notification_log_by_student(student_id, from_record, to_record):
    if student_id:
        logs = NotificationLog.objects.filter(
            student=student_id).order_by('-created_on')[from_record:to_record]
        count = NotificationLog.objects.filter(student=student_id).count()
    else:
        logs = NotificationLog.objects.all().order_by(
            '-created_on')[from_record:to_record]
        count = NotificationLog.objects.all().count()

    return logs, count


def query_route_data_by_student(student):
    locations_with_student = BusLocationWithStudents.objects.filter(
        student=student)

    result = []
    for location_with_student in locations_with_student:
        bus_route_with_location = BusRouteWithLocation.objects.filter(
            bus_location=location_with_student.bus_location).first()

        bus_route = bus_route_with_location.bus_route
        result.append([bus_route.route_type, location_with_student])

    return result


def query_absence_by_student(student_id, from_record, to_record):
    student = Student.objects.get(pk=student_id)
    result = query_route_data_by_student(student)

    if len(result) > 2:
        print('THIS IS WRONG. CURRENTLY ONLY SUPPORT MAXIMUM 2 ROUTES')
        return None

    attendance_sets = []
    labels = []
    for index, data in enumerate(result):
        labels.append(data[0])
        attendances = Attendance.objects.filter(
            bus_location_with_student=data[1], status=STUDENT_STATUS[2]
            [0]).order_by('-current_date')[from_record:to_record]
        attendance_sets.append(attendances)

    response = {}
    for index, attendance_set in enumerate(attendance_sets):
        for attendance in attendance_set:
            key = attendance.current_date.strftime('%Y/%m/%d')
            data = {'type': labels[index], 'absence': True}
            if key in response:
                response[key].append(data)
            else:
                response[key] = [data]

    data = []
    for key in sorted(response):
        value = response[key]
        if len(value) == 1:
            value.append({
                'type': "P" if value[0]['type'] == "D" else "D",
                'absence': False
            })
        d = key.split('/')
        data.append({'date': "%s/%s/%s" % (d[2], d[1], d[0]), 'values': value})
    return data


def query_contacts_of_student(student_id):
    student = Student.objects.filter(id=student_id).first()

    if not student:
        raise NotFound(detail=_('Student not exists'))

    contacts = Contact.objects.filter(parent=student.parent)

    additional_contacts = []

    if len(contacts) > 0:
        for contact in contacts:
            if contact.name is None:
                contact.name = ''
            additional_contacts.append(ContactSerializer(contact).data)

    default_contact = {
        'name':
        student.parent.info.first_name + " " + student.parent.info.last_name,
        'relationship': student.parent.relationship,
        'phone': student.parent.phone_number
    }
    result = {'default': default_contact, 'contacts': additional_contacts}
    return result


@transaction.atomic
def delete_absence_of_student(student, date):
    current_date = convert_str_to_date(date)
    locations_with_student = BusLocationWithStudents.objects.filter(
        student__pk=student)

    attendances = Attendance.objects.filter(
        current_date=current_date,
        bus_location_with_student__in=locations_with_student,
        status=STUDENT_STATUS[2][0])

    for attendance in attendances:
        attendance.delete()


def resolve_status_to_messaage(status_code):
    return NotificationTemplate.objects.filter(
        notification_type=status_code).first()


def query_students_from_next_location(location_id):
    bus_route_with_location = BusRouteWithLocation.objects.filter(
        bus_location__pk=location_id).first()
    order = bus_route_with_location.order
    route = bus_route_with_location.bus_route

    route_with_next_location = BusRouteWithLocation.objects.filter(
        order__gt=order, bus_route=route).order_by('order').first()

    if route_with_next_location is None:
        return None, None

    students_with_next_location = BusLocationWithStudents.objects.filter(
        bus_location=route_with_next_location.bus_location)
    return [
        student_with_next_location.student
        for student_with_next_location in students_with_next_location
    ], route_with_next_location


def notify_parent_of_next_stop(location_id):
    students, route_with_next_location = query_students_from_next_location(
        location_id)

    if students is None and route_with_next_location is None:
        return

    total_time = route_with_next_location.estimated_travelling_time + sum(
        int(t) for t in route_with_next_location.delay_time.split(';'))
    route = route_with_next_location.bus_route

    parents = Parent.objects.filter(children__in=students)
    message = "%s minutes to come" % total_time
    data = []
    for student in students:
        data.append((student, student.parent))

    for info in data:
        print('Send time notification to parent..... ')
        print(message)

        send_notification_to_parents({
            'parent': info[1].info,
            'title': _('Update student status'),
            'body': message,
            'route_id': route.pk,
            'supervisor': None,
            'student_id': info[0].pk
        })


def notify_parent(result, title, route_id, supervisor):
    for info in result:
        parents = Parent.objects.filter(children=info[0].pk)
        template = resolve_status_to_messaage(info[1].status)

        for parent in parents:
            lang = parent.preferred_language
            body = ""
            if template:
                body = template.en_text if lang == "en-US" else template.vn_text
            body = body.replace("<student-name> ", "")

            send_notification_to_parents({
                'parent':
                parent.info,
                'title':
                title or _('Update student status'),
                'body':
                "%s %s" % (info[0].name, body),
                'route_id':
                route_id,
                'supervisor':
                supervisor,
                'student_id':
                info[0].pk
            })
