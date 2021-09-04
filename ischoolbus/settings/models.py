from django.db import models
from django.utils.translation import ugettext_lazy as _

from infra.models import BaseModel


class Language(BaseModel):
    code = models.CharField(max_length=50, default="vi")
    name = models.CharField(max_length=200, default="Tiếng Việt")

    def __str__(self):
        return "%s - %s" % (self.code, self.name)


class SystemConfiguration(BaseModel):
    key = models.CharField(max_length=200)
    value = models.CharField(max_length=500)

    class Meta:
        verbose_name_plural = _('System Configuration')

    def __str__(self):
        return self.key
