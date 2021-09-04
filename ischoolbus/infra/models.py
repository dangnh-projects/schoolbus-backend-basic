from django.db import models


class BaseModel(models.Model):
    created_on = models.DateTimeField(editable=False, auto_now_add=True)
    created_by = models.IntegerField(editable=False, blank=True, null=True)
    updated_on = models.DateTimeField(editable=False, auto_now=True)
    updated_by = models.IntegerField(editable=False, blank=True, null=True)

    class Meta:
        abstract = True
