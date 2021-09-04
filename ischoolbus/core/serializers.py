from rest_framework import serializers
from .models import Bus, Parent, BusSupervisor, Driver, BusRoute, BusLocation, Student, \
    BusRouteWithLocation, BusLocationWithStudents, School, Attendance, \
    NotificationLog, NotificationTemplate, Contact
from dateutil import parser

from django.utils import timezone


class StdudentConfirmationDataSerializer(serializers.Serializer):
    pk = serializers.IntegerField()
    name = serializers.CharField(max_length=100)
    status_code = serializers.IntegerField()


class StudentConfirmSubmissionSerializer(serializers.Serializer):
    info = StdudentConfirmationDataSerializer(many=True)


class ParentInfoSerializer(serializers.ModelSerializer):
    pass


class BusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bus
        fields = "__all__"


class SchoolSerializer(serializers.ModelSerializer):
    class Meta:
        model = School
        fields = "__all__"


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = "__all__"


class StudentSerializer(serializers.ModelSerializer):
    school = SchoolSerializer()

    class Meta:
        model = Student
        fields = '__all__'


class NotificationTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationTemplate
        fields = '__all__'


class ParentListSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source='info.first_name')
    last_name = serializers.CharField(source='info.last_name')
    username = serializers.CharField(source='info.username')
    email = serializers.CharField(source='info.email')

    children = serializers.SerializerMethodField("_get_children")

    def _get_children(self, obj):
        children = Student.objects.filter(parent=obj)
        return StudentSerializer(children, many=True).data

    class Meta:
        model = Parent
        fields = '__all__'
        extra_fields = [
            'first_name', 'last_name', 'children', 'username', 'email'
        ]


class BusSupervisorSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField("_get_user_name")
    first_name = serializers.CharField(source='info.first_name')
    last_name = serializers.CharField(source='info.last_name')
    email = serializers.CharField(source='info.email')

    def _get_user_name(self, obj):
        if obj.info:
            return obj.info.username
        return ""

    class Meta:
        model = BusSupervisor
        fields = '__all__'
        extra_fields = ['user_name', 'first_name', 'last_name', 'email']


class DriverSerializer(serializers.ModelSerializer):
    class Meta:
        model = Driver
        fields = '__all__'


class BusRouteSerializer(serializers.ModelSerializer):
    bus_supervisor = BusSupervisorSerializer()
    driver = DriverSerializer()
    bus = BusSerializer()
    students = serializers.SerializerMethodField("_get_students")

    def _get_students(self, obj):
        bus_route_with_locations = BusRouteWithLocation.objects.filter(
            bus_route=obj)
        locations = [item.bus_location for item in bus_route_with_locations]
        bus_location_students = BusLocationWithStudents.objects.filter(
            bus_location__in=locations)

        students = [{
            "student": StudentSerializer(item.student).data,
            "location": BusLocationSerializer(item.bus_location).data
        } for item in bus_location_students]

        return students

    class Meta:
        model = BusRoute
        fields = '__all__'


class BusLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusLocation
        fields = '__all__'


class BusRouteWithLocationSerializer(serializers.ModelSerializer):
    bus_location = BusLocationSerializer()
    bus_route = BusRouteSerializer()

    class Meta:
        model = BusRouteWithLocation
        fields = '__all__'


class StudentCrudSerializer(serializers.ModelSerializer):
    parent = ParentListSerializer(read_only=True)
    bus_routes = serializers.SerializerMethodField("_get_routes")

    def _get_routes(self, student):
        bus_location_with_students = BusLocationWithStudents.objects.filter(
            student=student)

        bus_locations = [
            item.bus_location for item in bus_location_with_students
        ]

        bus_routes = [{
            "route": BusRouteSerializer(item.bus_route).data,
            "location": BusLocationSerializer(item.bus_location).data
        } for item in BusRouteWithLocation.objects.filter(
            bus_location__in=bus_locations)]

        return bus_routes

    def to_internal_value(self, value):
        value['dob'] = parser.parse(value['dob']).date()
        return super().to_internal_value(value)

    class Meta:
        model = Student
        fields = '__all__'
        extra_fields = ['bus_routes']


class BusLocationWithStudentsSerializer(serializers.ModelSerializer):
    student = StudentCrudSerializer()
    bus_location = BusLocationSerializer()

    class Meta:
        model = BusLocationWithStudents
        fields = '__all__'


class AttendanceSerializer(serializers.ModelSerializer):
    bus_location_with_student = BusLocationWithStudentsSerializer()

    class Meta:
        model = Attendance
        fields = '__all__'


class NotificationLogSerializer(serializers.ModelSerializer):
    datetime = serializers.SerializerMethodField("_get_logging_time")

    def _get_logging_time(self, obj):
        return timezone.localtime(obj.logging_time).strftime("%d/%m/%Y %H:%M")

    class Meta:
        model = NotificationLog
        fields = [
            "route_type",
            "datetime",
            "route_name",
            "sender",
            "receiver",
            "content",
        ]
