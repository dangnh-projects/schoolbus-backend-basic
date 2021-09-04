from django.contrib import admin
from django.utils.html import format_html
from infra.admin import ModelAdmin
from .models import Parent, School, Student, BusLocationWithStudents, BusRouteWithLocation, BusRoute, Bus, \
    BusSupervisor, Driver, BusLocation, Attendance, Contact
from daterangefilter.filters import PastDateRangeFilter


class AttendanceAdmin(ModelAdmin):
    list_display = ('pk', 'current_date', 'status',
                    'bus_location_with_student',
                    'reason_for_absence_or_missing')

    list_filter = ['status', ('current_date', PastDateRangeFilter)]


class DriverAdmin(ModelAdmin):
    pass


class BusLocationAdmin(ModelAdmin):
    list_display = ('pk', 'address', 'street', 'ward', 'district', 'province',
                    'lat', 'lng')


class BusAdmin(ModelAdmin):
    pass


class BusSupervisorAdmin(ModelAdmin):
    def name(self, obj):
        return "%s %s" % (obj.info.first_name, obj.info.last_name)

    list_display = ('pk', 'name')


class BusRouteAdmin(ModelAdmin):
    list_display = ('pk', 'name', 'is_running', 'start_time')


class BusLocationWithStudentsAdmin(ModelAdmin):
    list_display = ('pk', 'bus_location', 'student')


class BusRouteWithLocationAdmin(ModelAdmin):
    list_display = ('pk', 'bus_location', 'bus_route', 'order', 'status',
                    'estimated_travelling_time')


class ContactAdminInline(admin.StackedInline):
    model = Contact
    extra = 0


class StudentAdmin(ModelAdmin):
    def school(self, obj):
        return "%s" % (obj.school.name)

    list_display = ('pk', 'name', 'school', 'parent')


class SchoolAdmin(ModelAdmin):
    list_display = ('pk', 'name')


class ParentAdmin(ModelAdmin):
    def contact(self, obj):
        contacts = Contact.objects.filter(parent=obj)
        data = ""
        for contact in contacts:
            data += "<li>%s: %s - %s</li>" % (contact.relationship,
                                              contact.name, contact.phone)
        return format_html("<ul>%s</ul>" % data)

    def name(self, obj):
        return "%s %s" % (obj.info.first_name, obj.info.last_name)

    contact.allow_tags = True
    contact.short_description = 'Alternative contact'
    list_display = ('pk', 'info', 'name', 'contact')

    inlines = [
        ContactAdminInline,
    ]


admin.site.register(Attendance, AttendanceAdmin)
admin.site.register(Driver, DriverAdmin)
admin.site.register(BusSupervisor, BusSupervisorAdmin)
admin.site.register(BusLocation, BusLocationAdmin)
admin.site.register(Bus, BusAdmin)
admin.site.register(BusRoute, BusRouteAdmin)
admin.site.register(BusLocationWithStudents, BusLocationWithStudentsAdmin)
admin.site.register(BusRouteWithLocation, BusRouteWithLocationAdmin)
admin.site.register(Student, StudentAdmin)
admin.site.register(School, SchoolAdmin)
admin.site.register(Parent, ParentAdmin)

admin.site.site_header = 'NHG iSchoolBus'
admin.site.index_title = 'NHG iSchoolBus Administration'
admin.site.site_title = 'NHG iSchoolBus Administration'
