# Create your views here.
from rest_framework import viewsets
from .. import models
from . import serializers
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters



class BotSettingsView(viewsets.ModelViewSet):
    search_fields = 'key'
    serializer_class = serializers.SettingsSerializers
    filter_backends = [DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['key', 'for_futuer','for_spot']
    ordering_fields = '__all__'
    queryset = models.BotSettings.objects.all()

