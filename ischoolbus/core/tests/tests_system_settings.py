from django.test import TestCase, Client
from rest_framework.test import APIClient

from django.contrib.auth.models import User
from core.models import *
from .utils import *
from django.urls import reverse
import json
from datetime import datetime, timedelta

from unittest import skip


class SystemSettings(TestCase):
    def setUp(self):
        parent, supervisor, school, students, driver = prepare_people()
        bus_route_1, bus_route_2 = prepare_bus_route(driver, supervisor)
        to_school, to_home = prepare_location([bus_route_1, bus_route_2])
        prepare_student_with_location(students, to_school, to_home)

        self.client = APIClient()
        self.tokens = self.login()

    def login(self):
        usernames = ["supervisor1", "parent1", "parent2"]
        tokens = []
        for username in usernames:
            response = self.client.post(reverse("LoginView"),
                                        data={
                                            "username": username,
                                            "password": "12345678",
                                            "device_id": "1234",
                                            "device_token": "1234",
                                            "device_type": "android"
                                        })
            tokens.append(response.data["data"]["token"]["access"])

        return dict((key, value) for key, value in zip(usernames, tokens))

    def test_create_notification_template(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer %s" %
                                self.tokens["supervisor1"])
        data = {
            1: {
                "en_text": "<student-name> has missed the bus",
                "vn_text": "<student-name> đã lỡ chuyến xe hôm nay"
            },
            2: {
                "en_text": "<student-name> is absent today",
                "vn_text": "<student-name> đã báo vắng mặt hôm nay"
            },
            3: {
                "en_text": "<student-name> onboarded to school",
                "vn_text": "<student-name> đã lên xe bus. Khởi hành tới trường"
            },
            4: {
                "en_text": "<student-name> onboarded to home",
                "vn_text": "<student-name> đã lên xe. Bắt đầu về nhà"
            },
            5: {
                "en_text": "<student-name> reached school",
                "vn_text": "<student-name> đã tới trường"
            },
            6: {
                "en_text": "<student-name> reached home",
                "vn_text": "<student-name> đã về tới trạm"
            },
        }

        self.client.post(reverse("NotificationTemplateView"),
                         data=data,
                         format="json")

        response = self.client.get(reverse("NotificationTemplateView"),
                                   format="json")
        self.assertIsNotNone(response)

        for key, value in data.items():
            self.assertEqual(response.data["data"][key]["en_text"],
                             value["en_text"])
