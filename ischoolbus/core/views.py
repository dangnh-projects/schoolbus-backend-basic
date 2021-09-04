from django.conf import settings
from django.utils.translation import gettext as _
from django.utils import timezone

from rest_framework.exceptions import NotFound
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from infra.views import ProtectedView, CrudView
from infra.api_response import CommonResponse

from .serializers import ParentListSerializer, BusSerializer, \
    BusSupervisorSerializer, BusRouteSerializer, DriverSerializer, BusLocationSerializer, \
    StudentCrudSerializer, BusRouteWithLocationSerializer, BusLocationWithStudentsSerializer, \
    AttendanceSerializer, NotificationLogSerializer, NotificationTemplateSerializer, ContactSerializer
from .models import Parent, Bus, BusSupervisor, BusRoute, BusLocation, Driver, Student, NotificationLog, \
    NotificationTemplate, Contact

from .services import query_journey, start_journey, \
    query_bus_info_for_supervisor, query_next_stop_students, \
    create_driver, update_driver, create_parent, update_parent, \
    create_supervisor, update_supervisor, save_bus_route, save_bus_location, \
    get_route_locations, query_students_for_parent, query_student_estimation_for_parent, \
    get_parent_by_id_number, get_bus_route_by_type, assign_student_to_route, set_student_onbus, \
    create_student, update_student, \
    query_students_from_route, update_student_status_of_route, update_student_status_at_location, \
    query_attendances_and_location_of_bus_route, end_journey, send_notification_to_parents, query_moving_routes, \
    update_location_to_passed, update_bus_location, notify_start_journey, \
    update_delay_time, query_routes_of_student, set_absence_for_student, get_routes_by_bus, get_routes_by_driver, \
    get_routes_by_bus_supervisor, \
    update_bus_route_with_location, remove_student_with_location, \
    get_notification_template, create_or_update_notification_template, \
    query_route_info_by_student, query_notification_log_by_student, query_absence_by_student, query_contacts_of_student, \
    create_contact, update_contact, delete_absence_of_student, notify_parent, notify_parent_of_next_stop

import math
import json


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_students_for_parent(request):
    user = request.user
    students = query_students_for_parent(user)
    return CommonResponse.of(students)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_contacts_for_student(request, student_id):
    contacts = query_contacts_of_student(student_id)
    return CommonResponse.of(contacts)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_student_estimation_for_parent(request, student_id, route_id):
    student = query_student_estimation_for_parent(student_id, route_id)
    return CommonResponse.of(student)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def set_absence(request):
    student = request.POST['student_id']
    location_id = request.POST.get('location_id', '')
    message = request.POST['message']
    from_date = request.POST['from']
    to_date = request.POST['to']
    by_parent = request.POST.get('by_parent', False)
    set_absence_for_student(location_id.split(','), student, from_date,
                            to_date, message, by_parent)
    result = [{'id': student, 'notification_sent': True}]

    return CommonResponse.of(result)


class StartJourneyView(ProtectedView):
    def post(self, request, journey_type):
        content = []
        user = request.user
        route_id = start_journey(user, journey_type)
        if route_id is not None:
            notify_start_journey(route_id, journey_type)
            journeys = query_journey(route_id)
            journey_id = journeys['journey']['locations'][0]['id']
            students = query_next_stop_students(journey_id)
            journeys['next_stop_students'] = students

            return CommonResponse.of(journeys)
        return CommonResponse.of_errors("There is no bus to start")


class NextStopView(ProtectedView):
    def post(self, request, *args, **kwargs):
        user = request.user
        location_id = kwargs["location_id"]
        students = query_next_stop_students(location_id)
        return CommonResponse.of(students)


class BusInfoSupervisorView(ProtectedView):
    def get(self, request):
        supervisor = BusSupervisor.objects.filter(info=request.user.pk).first()
        content = query_bus_info_for_supervisor(supervisor.pk)
        return CommonResponse.of(content)


class BusView(CrudView):
    Model = Bus
    Serializer = BusSerializer
    search_fields = [
        "vehicle_registration_plate__icontains", "name__icontains",
        "brand__icontains"
    ]


class ContactView(CrudView):
    Model = Contact
    Serializer = ContactSerializer
    search_fields = ["name__icontains", "phone__icontains"]
    name = "Contact"

    def post(self, request):
        contact = create_contact(request)
        serializer = self._get_serializer()(contact)
        return CommonResponse.of(serializer.data)

    def put(self, request, *args, **kwargs):
        contact = update_contact(request, kwargs["pk"])
        return CommonResponse.of({
            "message": self._get_name() + " updated successfully",
            "data": self._get_serializer()(contact).data
        })


class BusSupervisorView(CrudView):
    Model = BusSupervisor
    Serializer = BusSupervisorSerializer
    name = "Bus Supervisor"

    search_fields = [
        "info__first_name__icontains", "info__last_name__icontains"
    ]

    def post(self, request):
        supervisor = create_supervisor(request)
        serializer = self._get_serializer()(supervisor)
        return CommonResponse.of(serializer.data)

        # save bus supervisor

    def put(self, request, *args, **kwargs):
        supervisor = update_supervisor(request, kwargs["pk"])
        return CommonResponse.of({
            "message":
            self._get_name() + " updated successfully",
            "data":
            self._get_serializer()(supervisor).data
        })


class StudentCrudView(CrudView):
    Model = Student
    Serializer = StudentCrudSerializer
    name = 'Student'

    search_fields = [
        "name__icontains", "alternative_name__icontains",
        "classroom__icontains"
    ]

    def post(self, request):
        student = create_student(request)
        serializer = self._get_serializer()(student)
        return CommonResponse.of(serializer.data)

    def put(self, request, *args, **kwargs):
        student = update_student(request, kwargs["pk"])
        return CommonResponse.of({
            "message": self._get_name() + " updated successfully",
            "data": self._get_serializer()(student).data
        })


class ParentListView(CrudView):
    Model = Parent
    Serializer = ParentListSerializer
    name = "Parent"

    search_fields = [
        "info__first_name__icontains", "info__last_name__icontains"
    ]

    def post(self, request):
        parent = create_parent(request)
        serializer = self._get_serializer()(parent)
        return CommonResponse.of(serializer.data)

    def put(self, request, *args, **kwargs):
        parent = update_parent(request, kwargs["pk"])
        return CommonResponse.of({
            "message": self._get_name() + " updated successfully",
            "data": self._get_serializer()(parent).data
        })

    def delete(self, request, *args, **kwargs):
        pk = kwargs["pk"]
        item = self._get_model().objects.filter(info=pk).first()
        if not item:
            raise NotFound()

        item.delete()
        return CommonResponse.of(
            {"message": self._get_name() + " removed successfully"})


class RouteView(CrudView):
    Model = BusRoute
    Serializer = BusRouteSerializer
    name = "Bus route"

    search_fields = ["name__icontains"]

    def post(self, request):
        location = save_bus_route(request)
        serializer = self._get_serializer()(location)
        return CommonResponse.of(serializer.data)


class BusLocationView(CrudView):
    Model = BusLocation
    Serializer = BusLocationSerializer
    name = "Bus location"

    def post(self, request):
        location = save_bus_location(request)
        serializer = self._get_serializer()(location)
        return CommonResponse.of(serializer.data)

    def put(self, request, *args, **kwargs):
        bus_location = update_bus_location(request, kwargs["pk"])
        return CommonResponse.of({
            "message":
            self._get_name() + " updated successfully",
            "data":
            self._get_serializer()(bus_location).data
        })


class DriverView(CrudView):
    Model = Driver
    Serializer = DriverSerializer
    name = "Driver"

    search_fields = [
        "name__icontains", "phone__icontains", "id_number__icontains"
    ]

    def post(self, request):
        driver = create_driver(request)
        serializer = self._get_serializer()(driver)
        return CommonResponse.of(serializer.data)

    def put(self, request, *args, **kwargs):
        driver = update_driver(request, kwargs["pk"])

        return CommonResponse.of({
            "message": self._get_name() + " updated successfully",
            "data": self._get_serializer()(driver).data
        })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_bus_route_view(request):
    bus_route = save_bus_route(request)
    serializer = BusRouteSerializer(bus_route)
    return CommonResponse.of(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_route_locations_view(request, *args, **kwargs):
    pk = kwargs["pk"]
    locations = get_route_locations(pk)
    serializer = BusRouteWithLocationSerializer(locations, many=True)
    return CommonResponse.of(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_parent_by_id_number_view(request, *args, **kwargs):
    id_number = kwargs["id_number"]
    parent, students = get_parent_by_id_number(id_number)
    return CommonResponse.of({
        "parent":
        ParentListSerializer(parent).data,
        "children":
        StudentCrudSerializer(students, many=True).data
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_routes_by_type_view(request, *args, **kwargs):
    route_type = kwargs["route_type"]
    routes = get_bus_route_by_type(route_type)

    serializer = BusRouteSerializer(routes, many=True)

    return CommonResponse.of({"routes": serializer.data})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def assign_student_to_route_view(request):
    route = request.POST["route"]
    location = request.POST["location"]
    student = request.POST["student"]

    if int(route) == -1:
        remove_student_with_location(location, student)
        return CommonResponse.of({"message": 'Remove successful'})

    bus_location_student = assign_student_to_route(route=route,
                                                   location=location,
                                                   student=student)

    serializer = BusLocationWithStudentsSerializer(bus_location_student)

    return CommonResponse.of({"bus_location_student": serializer.data})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def query_students_from_route_view(request, route):
    data = query_students_from_route(route)
    return CommonResponse.of(data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def update_status_at_location(request):
    data = json.loads(request.POST['students'])
    location_id = request.POST['location_id']
    route_id = request.POST['route_id']
    result = update_student_status_at_location(data, location_id)
    update_location_to_passed([record['pk'] for record in data],
                              route_id=route_id)
    notify_parent_of_next_stop(location_id)
    notify_parent(
        result,
        _("Student status on %s" %
          (timezone.localtime(timezone.now()).strftime("%d/%m/%Y %H:%M"))),
        route_id, request.user)
    return CommonResponse.of(data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def confirm_to_bus(request):
    data = json.loads(request.POST['students'])
    route_id = request.POST['route_id']
    result = update_student_status_of_route(data, route_id)
    notify_parent(
        result,
        _("Student status on %s" %
          (timezone.localtime(timezone.now()).strftime("%d/%m/%Y %H:%M"))),
        route_id, request.user)
    return CommonResponse.of(data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def confirm_to_school(request):
    data = json.loads(request.POST['students'])
    route_id = request.POST['route_id']
    result = update_student_status_of_route(data, route_id)
    notify_parent(
        result,
        _("Student status on %s" %
          (timezone.localtime(timezone.now()).strftime("%d/%m/%Y %H:%M"))),
        route_id, request.user)
    end_journey(route_id)
    return CommonResponse.of(data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def finish_journey(request, route):
    end_journey(route)
    return CommonResponse.of({'route': route})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def query_attendances_for_bus_route_view(request, *args, **kwargs):
    route = kwargs["route"]
    attendances, _ = query_attendances_and_location_of_bus_route(route)
    return CommonResponse.of(
        {"attendances": AttendanceSerializer(attendances, many=True).data})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def query_moving_route_view(request):
    moving_routes = query_moving_routes()
    return CommonResponse.of({"routes": moving_routes})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def send_notification_to_parents_view(request):
    parents = json.loads(request.POST["parents"])
    title = request.POST["title"]
    body = request.POST["body"]
    for parent in parents:
        send_notification_to_parents({
            "pk": parent,
            "title": title,
            "body": body
        })

    return CommonResponse.of({"parents": parents})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def send_delay(request):
    minutes = int(request.POST.get("minutes", 0))
    route_id = int(request.POST["route_id"])
    locations = update_delay_time(minutes, route_id)
    return CommonResponse.of({'locations': locations})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_routes_by_bus_view(request, bus_id):
    routes = get_routes_by_bus(bus_id)

    return CommonResponse.of(
        {"routes": BusRouteSerializer(routes, many=True).data})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_routes_by_driver_view(request, driver_id):
    routes = get_routes_by_driver(driver_id)

    return CommonResponse.of(
        {"routes": BusRouteSerializer(routes, many=True).data})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_routes_by_bus_supervisor_view(request, bus_supervisor_id):
    routes = get_routes_by_bus_supervisor(bus_supervisor_id)

    return CommonResponse.of(
        {"routes": BusRouteSerializer(routes, many=True).data})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_routes_of_student(request, student_id):
    bus_locations = query_routes_of_student(student_id)
    return CommonResponse.of({'routes': bus_locations})


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_bus_route_with_location_view(request, pk):
    bus_route_with_location = update_bus_route_with_location(request, pk)
    return CommonResponse.of(
        BusRouteWithLocationSerializer(bus_route_with_location).data)


class NotificationTemplateView(ProtectedView):
    def post(self, request, *args, **kwargs):
        result = create_or_update_notification_template(request.data)
        return CommonResponse.of(
            NotificationTemplateSerializer(result, many=True).data)

    def get(self, request):
        result = get_notification_template()
        return CommonResponse.of(result)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def query_server_settings(request):
    data = {
        'server': {
            'current_time':
            timezone.localtime(timezone.now()).strftime("%d/%m/%Y %H:%M")
        }
    }
    return CommonResponse.of(data)


@api_view(["get"])
@permission_classes([IsAuthenticated])
def query_route_info_by_student_view(request):
    student_id = request.GET.get('student_id', None)
    student_id = int(student_id) if student_id else None

    route_type = request.GET.get('route_type', None)
    results = query_route_info_by_student(student_id, route_type)

    return CommonResponse.of(results)


@api_view(["get"])
@permission_classes([IsAuthenticated])
def query_log_messages(request):
    student_id = request.GET.get('student_id', None)
    student_id = int(student_id) if student_id else None
    page = int(request.GET.get('page', 0))
    records_per_page = int(
        request.GET.get('records_per_page', settings.MAX_RECORDS_PER_PAGE))

    low = page * records_per_page
    high = (page + 1) * records_per_page

    logs, count = query_notification_log_by_student(student_id, low, high)

    total_pages = math.ceil(count / (records_per_page * 1.0))
    results = NotificationLogSerializer(logs, many=True)

    return CommonResponse.of({
        "results": results.data,
        "count": count,
        "total_pages": total_pages
    })


@api_view(["get"])
@permission_classes([IsAuthenticated])
def query_absence_by_student_view(request, student):
    page = int(request.GET.get('page', 0))
    records_per_page = int(
        request.GET.get('records_per_page', settings.MAX_RECORDS_PER_PAGE))

    low = page * records_per_page
    high = (page + 1) * records_per_page

    result = query_absence_by_student(student, low, high)
    return CommonResponse.of({'results': result})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def delete_absence_of_student_view(request, student):
    date = request.POST.get('date', None)
    delete_absence_of_student(student, date)
    return CommonResponse.of({'success': True})
