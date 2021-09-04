from django.contrib import admin
from infra.models import BaseModel


class ModelAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        if issubclass(type(obj), BaseModel):
            if hasattr(obj, 'id') and obj.id is not None:
                obj.created_by = request.user.id
            obj.updated_by = request.user.id

        obj.save()
