from rest_framework import serializers
from .models import Language


class LanguageSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Language
        fields = ['code']
