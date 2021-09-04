from core.models import *
from django.contrib.auth.models import User
from datetime import datetime
from django.core.files import File


def create_parent(username, id_number):
    user = User.objects.create_user(username, 'abc@d.com', '12345678', first_name="Thai %s" % id_number, last_name="Tran")
    parent = Parent(birthday=datetime.strptime('1985-05-04', "%Y-%m-%d"),
                    phone_number="0988181818",
                    id_number=id_number,
                    info=user)
    parent.avatar.save('%s.png' % username,
                       File(open('core/tests/avatar.png', 'rb')))
    parent.save()
    return parent


def create_supervisor(username):
    user = User.objects.create_user(username, 'abc@d.com', '12345678', first_name="Thai %s" % username, last_name="Tran")
    supervisor = BusSupervisor(
        birthday=datetime.strptime('1985-05-04', "%Y-%m-%d"),
        phone_number="0988181818",
        start_working_date=datetime.strptime('1985-05-04', "%Y-%m-%d"),
        home_number="A9 Cu xa Dong Tien",
        ward="14",
        district="10",
        province="Ho Chi Minh",
        status="A",
        info=user)

    supervisor.avatar.save('%s.png' % username,
                           File(open('core/tests/avatar.png', 'rb')))
    supervisor.save()
    return supervisor


def create_school(name):
    school = School(name=name)
    school.logo.save("%s.png" % name, File(open('core/tests/avatar.png',
                                                'rb')))
    school.save()
    return school


def create_student(name, parent, school):
    student = Student(name=name,
                      alternative_name=name,
                      dob=datetime.strptime('2008-05-04', "%Y-%m-%d"),
                      classroom='3.2',
                      bus_registered_date=datetime.now().date(),
                      home_number='A9 Cu Xa Dong Tien',
                      street="Thanh Thai",
                      ward="14",
                      district="10",
                      province="Ho Chi Minh",
                      parent=parent,
                      school=school)
    student.image.save("%s.png" % name,
                       File(open('core/tests/avatar.png', 'rb')))

    student.save()
    return student


def create_driver(id_number):
    driver = Driver(id_number=id_number,
                    name=id_number,
                    phone="092991192211",
                    birthday=datetime.strptime('2008-05-04', "%Y-%m-%d"),
                    address="Earth",
                    start_working_date=datetime.now().date())

    driver.image.save("%s.png" % id_number,
                      File(open('core/tests/avatar.png', 'rb')))

    driver.save()
    return driver


def create_bus(name):
    bus = Bus(vehicle_registration_plate="99a-1921 22",
              name=name,
              brand="Brand",
              start_working_date=datetime.now().date(),
              number_of_seat=40)

    bus.save()
    return bus


def create_bus_route(name, bus, driver, supervisor, route_type):
    bus_route = BusRoute(name=name,
                         bus=bus,
                         driver=driver,
                         bus_supervisor=supervisor,
                         route_type=route_type,
                         estimated_start_time=datetime.now().time())

    bus_route.save()
    return bus_route


def create_bus_location(address, street, ward, district, province, order,
                        route):
    bus_location = BusLocation(address=address,
                               street=street,
                               ward=ward,
                               district=district,
                               province=province,
                               lat=10,
                               lng=10)
    bus_location.save()
    route_with_location = BusRouteWithLocation(bus_route=route,
                                               bus_location=bus_location,
                                               order=order,
                                               estimated_travelling_time=10)
    route_with_location.save()
    return bus_location


def prepare_people():
    parent = create_parent('parent1', "023212123")
    parent1 = create_parent('parent2', "023212122")
    supervisor = create_supervisor('supervisor1')
    school = create_school('UKA Binh Thanh')
    school1 = create_school('SNA Him Lam')

    students = [
        create_student("student 1", parent, school),
        create_student("student 2", parent, school),
        create_student("student 3", parent1, school1),
        create_student("student 4", parent1, school1)
    ]

    driver = create_driver("123123123")
    return (parent, supervisor, school, students, driver)


def prepare_bus_route(driver, supervisor):
    bus = create_bus("Bus so 1")
    bus_route_1 = create_bus_route('Route 001', bus, driver, supervisor, 'P')
    bus_route_2 = create_bus_route('Route 002', bus, driver, supervisor, 'D')
    return (bus_route_1, bus_route_2)


def prepare_location(bus_routes):
    school_points = [1, 2, 3, 4]
    home_points = [4, 3, 1]
    locations = []
    for index, points in enumerate([school_points, home_points]):
        order = 0
        way_locations = []
        for point in points:
            location = create_bus_location('address %s' % point,
                                           'street %s' % point,
                                           'ward %s' % point,
                                           'district %s' % point,
                                           'province %s' % point, order,
                                           bus_routes[index])
            order += 1
            way_locations.append(location)

        locations.append(way_locations)

    return tuple(locations)


def prepare_student_with_location(students, to_school, to_home):
    data = []
    data.append(
        BusLocationWithStudents(student=students[0],
                                bus_location=to_school[0]))
    data.append(
        BusLocationWithStudents(student=students[1],
                                bus_location=to_school[0]))
    data.append(
        BusLocationWithStudents(student=students[2],
                                bus_location=to_school[2]))
    data.append(
        BusLocationWithStudents(student=students[3],
                                bus_location=to_school[2]))

    data.append(
        BusLocationWithStudents(student=students[3], bus_location=to_home[1]))
    data.append(
        BusLocationWithStudents(student=students[2], bus_location=to_home[1]))
    data.append(
        BusLocationWithStudents(student=students[1], bus_location=to_home[2]))
    data.append(
        BusLocationWithStudents(student=students[0], bus_location=to_home[2]))

    BusLocationWithStudents.objects.bulk_create(data)
