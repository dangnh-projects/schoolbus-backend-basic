from django.test import TestCase, Client
from rest_framework.test import APIClient

from django.contrib.auth.models import User
from core.models import *
from .utils import *
from django.urls import reverse
import json
from datetime import datetime, timedelta

from unittest import skip


class BusRouteFlow(TestCase):
    def setUp(self):
        parent, supervisor, school, students, driver = prepare_people()
        bus_route_1, bus_route_2 = prepare_bus_route(driver, supervisor)
        to_school, to_home = prepare_location([bus_route_1, bus_route_2])
        prepare_student_with_location(students, to_school, to_home)

        self.client = APIClient()
        self.tokens = self.login()

    def login(self):
        usernames = ['supervisor1', 'parent1', 'parent2']
        tokens = []
        for username in usernames:
            response = self.client.post(reverse('LoginView'),
                                        data={
                                            'username': username,
                                            'password': '12345678',
                                            'device_id': '1234',
                                            'device_token': '1234',
                                            'device_type': 'android',
                                            'locale': 'vn-VN'
                                        })
            tokens.append(response.data['data']['token']['access'])

        return dict((key, value) for key, value in zip(usernames, tokens))

    def start_pickup(self, supervisor_token):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' +
                                supervisor_token)
        response = self.client.post(
            reverse('StartJourneyView', kwargs={'journey_type': 'pickup'}))
        return response

    def start_dropoff(self, supervisor_token):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' +
                                supervisor_token)
        response = self.client.post(
            reverse('StartJourneyView', kwargs={'journey_type': 'dropoff'}))
        return response

    def go_to_next_stop(self, location_id, supervisor_token):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' +
                                supervisor_token)
        response = self.client.post(
            reverse('NextStopView', kwargs={'location_id': location_id}))
        return response

    def update_status_at_location(self, data, route, location,
                                  supervisor_token):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' +
                                supervisor_token)
        response = self.client.post(reverse('update_status_at_location'),
                                    data={
                                        'students': data,
                                        'route_id': route,
                                        'location_id': location
                                    })
        return response

    def get_students_of_parent(self, parent_token):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + parent_token)
        response = self.client.get(reverse('get_students_for_parent'))
        return response

    def confirm_to_bus(self, supervisor_token, data, route):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' +
                                supervisor_token)
        response = self.client.post(reverse('confirm_to_bus'),
                                    data={
                                        'students': data,
                                        'route_id': route
                                    })

        return response

    def confirm_to_school(self, supervisor_token, data, route):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' +
                                supervisor_token)
        response = self.client.post(reverse('confirm_to_school'),
                                    data={
                                        'students': data,
                                        'route_id': route
                                    })

        return response

    def query_students_from_route_view(self, supervisor_token, route):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' +
                                supervisor_token)
        response = self.client.get(
            reverse('query_students_from_route_view', kwargs={'route': route}))
        return response

    def mark_all_students_on_the_way(self, supervisor_token, route, locations,
                                     first_status):
        student_status = {}
        for location in locations:
            res = self.go_to_next_stop(location['id'], supervisor_token)
            if len(res.data['data']) != 0:
                data = []
                location_id = -1
                for index, student in enumerate(res.data['data']):
                    status = first_status[index % len(first_status)]
                    data.append({"pk": student['id'], "status_code": status})
                    student_status[student['id']] = status
                    location_id = location['id']

                self.update_status_at_location(json.dumps(data), route,
                                               location_id, supervisor_token)

        return student_status

    def check_all_students_on_the_way(self, parents_tokens, student_status,
                                      bus_status):
        result = {}
        for token in parents_tokens:
            response = self.get_students_of_parent(token)
            students = []
            for student in response.data['data']:
                students.append(student['id'])
                self.assertEqual(student_status[student['id']],
                                 student['status_code'])
                self.assertEqual(bus_status, student['bus']['status_code'])
            result[token] = students

        return result

    def get_student_detail(self, parent_token, student, route):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + parent_token)
        response = self.client.get(
            reverse('get_student_estimation_for_parent',
                    kwargs={
                        'student_id': student,
                        'route_id': route
                    }))

        return response

    def finish_journey(self, supervisor_token, route):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' +
                                supervisor_token)
        response = self.client.post(
            reverse('finish_journey', kwargs={'route': route}))
        return response

    def set_dropoff_flow_running(self, first_status, second_status):
        response = self.start_dropoff(self.tokens['supervisor1'])
        locations = response.data['data']['journey']['locations']
        route = response.data['data']['journey']['route_id']

        # supervisor view list of students before confirm on bus
        student_init_status = {}
        response = self.query_students_from_route_view(
            self.tokens['supervisor1'], route)
        data = []
        student_first_status = {}
        for index, student in enumerate(response.data['data']):
            if student['report_absence_by_parent'] == True:
                self.assertEqual(2, student['status_code'])
                student_init_status[student['id']] = 2
            else:
                self.assertEqual(0, student['status_code'])
                student_init_status[student['id']] = 0
            status = first_status[index % len(first_status)]
            data.append({"pk": student['id'], 'status_code': status})
            student_first_status[student['id']] = status

        # check if the list screen of student on parent view is correct or not
        parent_students = self.check_all_students_on_the_way(
            [self.tokens['parent1'], self.tokens['parent2']],
            student_init_status, 2)

        # check if the detail screen of student on parent view is correct or not
        self.check_student_detail(parent_students, route, student_init_status,
                                  2)

        # supervisor confirm to bus
        self.confirm_to_bus(self.tokens['supervisor1'], json.dumps(data),
                            route)

        # check if the list screen of student on parent view is correct or not
        parent_students = self.check_all_students_on_the_way(
            [self.tokens['parent1'], self.tokens['parent2']],
            student_first_status, 2)

        # check if the detail screen of student on parent view is correct or not
        self.check_student_detail(parent_students, route, student_first_status,
                                  2)

        # update on the way
        student_second_status = self.mark_all_students_on_the_way(
            self.tokens['supervisor1'], route, locations, second_status)

        # check if the list screen of student on parent view is correct or not
        parent_students = self.check_all_students_on_the_way(
            [self.tokens['parent1'], self.tokens['parent2']],
            student_second_status, 2)

        # check if the detail screen of student on parent view is correct or not
        self.check_student_detail(parent_students, route,
                                  student_second_status, 2)

        # stop journey
        self.finish_journey(self.tokens['supervisor1'], route)
        parent_students = self.check_all_students_on_the_way(
            [self.tokens['parent1'], self.tokens['parent2']],
            student_second_status, 1)

    def set_pickup_flow_running(self, student_first_status_set,
                                student_second_status_set):
        # start
        response = self.start_pickup(self.tokens['supervisor1'])
        locations = response.data['data']['journey']['locations']
        route = response.data['data']['journey']['route_id']

        # update on the way
        student_first_status = self.mark_all_students_on_the_way(
            self.tokens['supervisor1'], route, locations,
            student_first_status_set)

        # check if the list screen of student on parent view is correct or not
        parent_students = self.check_all_students_on_the_way(
            [self.tokens['parent1'], self.tokens['parent2']],
            student_first_status, 0)

        # check if the detail screen of student on parent view is correct or not
        self.check_student_detail(parent_students, route, student_first_status,
                                  0)

        # supervisor reviews student list before confirm to school
        response = self.query_students_from_route_view(
            self.tokens['supervisor1'], route)
        data = []
        student_second_status = {}
        for index, student in enumerate(response.data['data']):
            self.assertEqual(student_first_status[student['id']],
                             student['status_code'])
            status = student_second_status_set[index %
                                               len(student_second_status_set)]
            data.append({"pk": student['id'], 'status_code': status})
            student_second_status[student['id']] = status

        # confirm to school
        self.confirm_to_school(self.tokens['supervisor1'], json.dumps(data),
                               route)

        # parent check again, status should be second status and bus status as stopped
        parent_students = self.check_all_students_on_the_way(
            [self.tokens['parent1'], self.tokens['parent2']],
            student_status=student_second_status,
            bus_status=1)

        # check if the detail screen of student on parent view is correct or not
        self.check_student_detail(parent_students,
                                  route,
                                  student_second_status,
                                  bus_status=1)

        self.assertEqual(False,
                         BusRoute.objects.filter(pk=route).first().is_running)

    def check_student_detail(self, parent_students, route, student_status,
                             bus_status):
        for token, students in parent_students.items():
            for student in students:
                response = self.get_student_detail(token, student, route)
                self.assertEqual(student_status[student],
                                 response.data['data']['status_code'])
                self.assertEqual(bus_status,
                                 response.data['data']['bus']['status_code'])

    def test_input(self):
        user = User.objects.filter(username='parent1').first()
        user2 = User.objects.filter(username='supervisor1').first()
        parent = Parent.objects.filter(info=user).first()
        supervisor = BusSupervisor.objects.filter(info=user2)
        no_driver = Driver.objects.all().count()
        routes = BusRoute.objects.all().count()
        routes_with_locations = BusRouteWithLocation.objects.all().count()
        no_bus = Bus.objects.all().count()
        number = len(Student.objects.filter(parent=parent))

        self.assertIsNotNone(parent)
        self.assertIsNotNone(supervisor)
        self.assertEqual(2, number)
        self.assertEqual(1, no_driver)
        self.assertEqual(1, no_bus)
        self.assertEqual(2, routes)
        self.assertEqual(7, routes_with_locations)

    def test_before_start_pickup(self):
        data = dict((student.pk, 0) for student in Student.objects.all())
        self.check_all_students_on_the_way(
            [self.tokens['parent1'], self.tokens['parent2']], data, 1)

    def test_dropoff_flow(self):
        data_set = [
            ([4, 4], [6, 6]),
            ([1, 1], [6, 6]),
            ([4, 4], [1, 1]),
            ([1, 1], [1, 1]),
            ([1, 4], [6, 6]),
            ([1, 4], [1, 1]),
            ([4, 1], [6, 6]),
            ([4, 1], [1, 1]),
        ]

        for first_status, second_status in data_set:
            self.set_dropoff_flow_running(first_status, second_status)

    def test_pickup_flow(self):
        data_set = [
            ([3, 3], [5, 5]),
            ([1, 1], [5, 5]),
            ([3, 3], [1, 1]),
            ([1, 1], [1, 1]),
            ([1, 3], [5, 5]),
            ([1, 3], [1, 1]),
            ([3, 1], [5, 5]),
            ([3, 1], [1, 1]),
        ]

        for first_status, second_status in data_set:
            self.set_pickup_flow_running(first_status, second_status)

    def test_pickup_and_dropoff(self):
        first_status, second_status = ([3, 3], [5, 5])
        self.set_pickup_flow_running(first_status, second_status)

        first_status, second_status = ([4, 4], [6, 6])
        self.set_dropoff_flow_running(first_status, second_status)

        first_status, second_status = ([1, 3], [5, 5])
        self.set_pickup_flow_running(first_status, second_status)

        first_status, second_status = ([1, 4], [6, 6])
        self.set_dropoff_flow_running(first_status, second_status)

    def get_routes_of_student(self, student, parent_token):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + parent_token)
        response = self.client.get(
            reverse('get_route_of_student', kwargs={'student_id': student}))
        return response

    def send_absence_by_parent(self, parent_token, student, location,
                               from_date, to_date):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + parent_token)
        response = self.client.post(reverse('set_absence'),
                                    data={
                                        'student_id': student,
                                        'location_id': location,
                                        'message': 'absence',
                                        'from': from_date,
                                        'to': to_date,
                                        'by_parent': True,
                                    })
        return response

    def running_cycle(self):
        first_status, second_status = ([3, 3], [5, 5])
        self.set_pickup_flow_running(first_status, second_status)

        first_status, second_status = ([4, 4], [6, 6])
        self.set_dropoff_flow_running(first_status, second_status)

        first_status, second_status = ([1, 1], [5, 5])
        self.set_pickup_flow_running(first_status, second_status)

        first_status, second_status = ([1, 4], [6, 6])
        self.set_dropoff_flow_running(first_status, second_status)

    def test_absence_dropoff(self):
        response = self.get_students_of_parent(self.tokens['parent1'])
        student = None
        location = None

        if len(response.data['data']) == 0:
            return

        student = response.data['data'][0]['id']
        response = self.get_routes_of_student(student, self.tokens['parent1'])
        routes = response.data['data']['routes']

        if 'D' in routes:
            location = routes['D'][0]['id']

        current_date = datetime.now().date()
        daydelta = 1
        from_date = current_date - timedelta(days=daydelta)
        to_date = current_date + timedelta(days=daydelta)

        response = self.send_absence_by_parent(
            self.tokens['parent1'],
            student,
            location,
            from_date=from_date.strftime("%d/%m/%Y"),
            to_date=to_date.strftime("%d/%m/%Y"))
        attendances = Attendance.objects.all()
        self.assertEqual(daydelta * 2 + 1, attendances.count())
        self.running_cycle()

    def test_absence_pickup(self):
        response = self.get_students_of_parent(self.tokens['parent1'])
        student = None
        location = None

        if len(response.data['data']) == 0:
            return

        student = response.data['data'][0]['id']
        response = self.get_routes_of_student(student, self.tokens['parent1'])
        routes = response.data['data']['routes']

        if 'P' in routes:
            location = routes['P'][0]['id']

        current_date = datetime.now().date()
        daydelta = 1
        from_date = current_date - timedelta(days=daydelta)
        to_date = current_date + timedelta(days=daydelta)

        response = self.send_absence_by_parent(
            self.tokens['parent1'],
            student,
            location,
            from_date=from_date.strftime("%d/%m/%Y"),
            to_date=to_date.strftime("%d/%m/%Y"))
        attendances = Attendance.objects.all()
        self.assertEqual(daydelta * 2 + 1, attendances.count())

        self.running_cycle()

    def test_absence(self):
        response = self.get_students_of_parent(self.tokens['parent1'])
        student = None
        location = None

        if len(response.data['data']) == 0:
            return

        student = response.data['data'][0]['id']
        response = self.get_routes_of_student(student, self.tokens['parent1'])
        routes = response.data['data']['routes']
        route_type = ['D', 'P']
        ids = []
        for t in route_type:
            if t in routes:
                ids.append(str(routes[t][0]['id']))
        location = ",".join(ids)
        current_date = datetime.now().date()
        daydelta = 1
        from_date = current_date - timedelta(days=daydelta)
        to_date = current_date + timedelta(days=daydelta)

        response = self.send_absence_by_parent(
            self.tokens['parent1'],
            student,
            location,
            from_date=from_date.strftime("%d/%m/%Y"),
            to_date=to_date.strftime("%d/%m/%Y"))

        self.running_cycle()

    def test_logging(self):
        self.running_cycle()

        # from dashboard view
        self.client.credentials(HTTP_AUTHORIZATION='Bearer %s' %
                                self.tokens['supervisor1'])
        response = self.client.get(reverse('query_log_messages'))
        self.assertIsNotNone(response.data['data']['results'])
        self.assertNotEqual(0, len(response.data['data']['results']))

        # from parent view
        response = self.get_students_of_parent(self.tokens['parent1'])
        student_id = response.data['data'][0]['id']
        response = self.client.get(reverse('query_log_messages'), {
            'student_id': str(student_id),
            'record_per_page': str(1)
        })
        self.assertIsNotNone(response.data['data']['results'])
        self.assertNotEqual(0, len(response.data['data']['results']))

    def query_route_info_for_parent(self, parent_token):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + parent_token)
        student = Student.objects.all().first()

        response = self.client.get(reverse('query_route_info_by_student_view'),
                                   data={
                                       'student_id': student.pk,
                                       'route_type': 'P'
                                   })
        return response

    def test_query_route_info_for_parent(self):
        response = self.query_route_info_for_parent(self.tokens['parent1'])
        self.assertIsNotNone(response.data)
        self.assertIsNotNone(response.data['data']['driver'])
        self.assertIsNotNone(response.data['data']['supervisor'])
        self.assertIsNotNone(response.data['data']['locations'])
        self.assertIsNotNone(response.data['data']['bus'])

    def query_absence_by_student(self, parent_token):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + parent_token)
        student = Student.objects.all().first()

        response = self.client.get(
            reverse('query_absence_by_student_view',
                    kwargs={
                        'student': student.pk,
                    }))
        return response

    def delete_absence_of_student_view(self, parent_token):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + parent_token)
        student = Student.objects.all().first()
        current_date = datetime.now().date()
        response = self.client.post(
            reverse('delete_absence_of_student_view',
                    kwargs={
                        'student': student.pk,
                    }),
            data={'date': current_date.strftime("%d/%m/%Y")})
        return response

    def test_query_absence_by_student(self):
        current_date = datetime.now().date()
        daydelta = 3
        from_date = current_date - timedelta(days=daydelta)
        to_date = current_date + timedelta(days=daydelta)

        student = Student.objects.all().first()
        response = self.get_routes_of_student(student.pk,
                                              self.tokens['parent1'])
        routes = response.data['data']['routes']

        location = None
        if 'D' in routes:
            location = routes['D'][0]['id']

        response = self.send_absence_by_parent(
            self.tokens['parent1'],
            student.pk,
            location,
            from_date=from_date.strftime("%d/%m/%Y"),
            to_date=to_date.strftime("%d/%m/%Y"))

        res = self.query_absence_by_student(self.tokens['parent1'])

        self.assertIsNotNone(res.data['data']['results'])
        self.assertEqual(len(res.data['data']['results']),
                         daydelta * 2 + 1)

        res = self.delete_absence_of_student_view(self.tokens['parent1'])

        res = self.query_absence_by_student(self.tokens['parent1'])

        self.assertIsNotNone(res.data['data']['results'])
        self.assertEqual(len(res.data['data']['results']),
                         daydelta * 2)
