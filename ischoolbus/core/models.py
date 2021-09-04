from django.db import models
from django.contrib.auth.models import User

from infra.models import BaseModel
from .constants import ROUTE_TYPE


class School(BaseModel):
    name = models.CharField(max_length=200)
    logo = models.FileField(upload_to='schools', max_length=100)

    def __str__(self):
        return self.name


class Parent(BaseModel):
    birthday = models.DateField(auto_now=False, auto_now_add=False)
    phone_number = models.CharField(max_length=50)
    relationship = models.CharField(max_length=50)
    email = models.CharField(max_length=100, null=True, blank=True)
    avatar = models.FileField(upload_to='parents', max_length=100)
    preferred_language = models.CharField(max_length=100, default="en-US")
    id_number = models.CharField(max_length=50, unique=True)

    info = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
    )

    def __str__(self):
        return "%s %s (%s)" % (self.info.first_name, self.info.last_name,
                               self.info)


class Student(BaseModel):
    name = models.CharField(max_length=500)

    image = models.ImageField(upload_to='students', blank=True)
    alternative_name = models.CharField(max_length=255, null=True, blank=True)
    dob = models.DateField(default=None)
    classroom = models.CharField(max_length=20, blank=True, null=True)
    bus_registered_date = models.DateField(default=None, null=True, blank=True)

    home_number = models.CharField(max_length=100, blank=True, null=True)
    street = models.CharField(max_length=200, blank=True, null=True)
    ward = models.CharField(max_length=100, blank=True, null=True)
    district = models.CharField(max_length=200, blank=True, null=True)
    province = models.CharField(max_length=200, blank=True, null=True)

    parent = models.ForeignKey(Parent,
                               related_name="children",
                               on_delete=models.CASCADE,
                               default=None,
                               null=True,
                               blank=True)

    school = models.ForeignKey(School,
                               on_delete=models.CASCADE,
                               default=None,
                               null=True,
                               blank=True)

    def __str__(self):
        return self.name


class Contact(BaseModel):
    name = models.CharField(max_length=200, blank=True, null=True)
    relationship = models.CharField(max_length=200)
    phone = models.CharField(max_length=200)

    parent = models.ForeignKey(Parent,
                               related_name='parent',
                               on_delete=models.CASCADE,
                               default=None,
                               null=True,
                               blank=True)

    def __str__(self):
        return "%s %s (%s)" % (self.name, self.relationship,
                               self.phone)


class Driver(BaseModel):
    id_number = models.CharField(max_length=100)
    name = models.CharField(max_length=200, blank=True, null=True)
    image = models.ImageField(upload_to='drivers', blank=True, null=True)
    phone = models.CharField(max_length=50)

    enabled = models.BooleanField(default=True)
    birthday = models.DateField(auto_now=False, auto_now_add=False)
    address = models.CharField(max_length=255)
    start_working_date = models.DateField(auto_now=False, auto_now_add=False)

    def __str__(self):
        return self.name


class Bus(BaseModel):
    vehicle_registration_plate = models.CharField(max_length=100)
    name = models.CharField(max_length=255)
    brand = models.CharField(max_length=50)
    start_working_date = models.DateField(auto_now=False, auto_now_add=False)
    number_of_seat = models.IntegerField()

    def __str__(self):
        return self.name


class BusSupervisor(BaseModel):
    birthday = models.DateField(auto_now=False, auto_now_add=False)
    phone_number = models.CharField(max_length=50)
    start_working_date = models.DateField(auto_now=False, auto_now_add=False)

    home_number = models.CharField(max_length=250)
    ward = models.CharField(max_length=250)
    district = models.CharField(max_length=250)
    province = models.CharField(max_length=250)

    status = models.CharField(max_length=1,
                              choices=[("A", "Active"), ("I", "Inactive")],
                              default="A")
    info = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.FileField(upload_to='supervisors', max_length=100)

    def __str__(self):
        return self.info.username


class BusLocation(BaseModel):
    address = models.CharField(max_length=100, blank=True, null=True)
    street = models.CharField(max_length=200, blank=True, null=True)
    ward = models.CharField(max_length=100, blank=True, null=True)
    district = models.CharField(max_length=100, blank=True, null=True)
    province = models.CharField(max_length=100, blank=True, null=True)
    lng = models.FloatField()
    lat = models.FloatField()

    polygon_to_next_location = models.TextField(blank=True, null=True)

    def __str__(self):
        return "%s %s, %s, %s" % (self.address, self.street, self.ward,
                                  self.district)


class BusRoute(BaseModel):
    name = models.CharField(max_length=100)

    bus = models.ForeignKey(Bus, on_delete=models.CASCADE)
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE)
    bus_supervisor = models.ForeignKey(BusSupervisor, on_delete=models.CASCADE)

    route_type = models.CharField(max_length=1,
                                  choices=ROUTE_TYPE.data,
                                  default=ROUTE_TYPE.default)
    is_running = models.BooleanField(default=False)
    estimated_start_time = models.TimeField(default=None,
                                            blank=True,
                                            null=True)

    estimated_end_time = models.TimeField(default=None, blank=True, null=True)

    start_time = models.DateTimeField(default=None, blank=True, null=True)
    end_time = models.DateTimeField(default=None, blank=True, null=True)

    def __str__(self):
        return "%s/%s - is_running: %s" % (self.name, self.route_type,
                                           self.is_running)


class BusRouteHistory(BaseModel):
    bus_route = models.ForeignKey(BusRoute, on_delete=models.CASCADE)
    status = models.IntegerField(choices=[(0, "Stopping"), (1, 'Running')],
                                 default=0)

    def __str__(self):
        return "%s" % self.bus_route


class BusRouteWithLocation(BaseModel):
    bus_route = models.ForeignKey(BusRoute, on_delete=models.CASCADE)
    bus_location = models.ForeignKey(BusLocation, on_delete=models.CASCADE)
    order = models.IntegerField(default=0)
    status = models.IntegerField(choices=[(0, "Not reach"), (1, 'Passed')],
                                 default=0)
    estimated_travelling_time = models.IntegerField(
        blank=True, null=True,
        default=0)  # estimated trevel time from previous point

    delay_time = models.CharField(default="0", max_length=100)

    class Meta:
        unique_together = ('order', 'bus_route')

    def __str__(self):
        return "%s: %s" % (self.bus_route.name, self.bus_location)


class BusLocationWithStudents(BaseModel):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    bus_location = models.ForeignKey(BusLocation, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('student', 'bus_location')

    def __str__(self):
        return "%s: %s at %s | %s" % (self.pk, self.student, self.bus_location,
                                      self.updated_on)


class NotificationTemplate(BaseModel):
    notification_type = models.IntegerField()
    vn_text = models.CharField(max_length=500)
    en_text = models.CharField(max_length=500)

    def __str__(self):
        return self.notification_type


class NotificationLog(BaseModel):
    route_type = models.CharField(max_length=100)
    route_name = models.CharField(max_length=500)
    logging_time = models.DateTimeField(editable=False, auto_now_add=True)
    sender = models.CharField(max_length=200)
    receiver = models.CharField(max_length=500, blank=True, null=True)
    student = models.IntegerField(blank=True, null=True)
    content = models.CharField(max_length=500)

    def __str__(self):
        return "%s to %s: %s" % (self.sender, self.receiver, self.content)


class Attendance(BaseModel):
    bus_location_with_student = models.ForeignKey(BusLocationWithStudents,
                                                  on_delete=models.CASCADE,
                                                  related_name="attendances")
    status = models.IntegerField()
    current_date = models.DateField()
    reason_for_absence_or_missing = models.TextField(blank=True, null=True)
    report_absence_by_parent = models.BooleanField(default=False)

    def __str__(self):
        return "%s => %s - status: %s / absence_by_parent: %s" % (
            self.current_date, self.bus_location_with_student, self.status,
            self.report_absence_by_parent)
