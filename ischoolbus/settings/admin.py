from django.contrib import admin
from .models import *
from infra.admin import ModelAdmin


class LanguageAdmin(ModelAdmin):
    pass


class SystemConfigurationAdmin(ModelAdmin):
    list_display = ('key', 'value')


admin.site.register(SystemConfiguration, SystemConfigurationAdmin)
admin.site.register(Language, LanguageAdmin)
