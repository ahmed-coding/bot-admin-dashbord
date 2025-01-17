from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets
from . import models
from . import serializers
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters



class SymbolView(viewsets.ModelViewSet):
    search_fields = 'symbol'
    serializer_class = serializers.SymbolSerializers
    filter_backends = [DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['symbol', 'win_rate']
    ordering_fields = '__all__'
    queryset = models.Symbol.objects.filter(win_rate__gt=50).order_by('avg_duration')
    # queryset = models.Symbol.objects.all().order_by('-avg_duration')

class FutuerSymbolView(viewsets.ModelViewSet):
    search_fields = 'symbol'
    serializer_class = serializers.SymbolSerializers
    filter_backends = [DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['symbol', 'win_rate']
    ordering_fields = '__all__'
    # queryset = models.FSymbol.objects.filter(win_rate__gt=70).order_by('win_rate')
    queryset = models.FSymbol.objects.all().order_by('win_rate')



class TradeView(viewsets.ModelViewSet):
    search_fields = ['is_open', 'symbol','is_futuer']
    serializer_class = serializers.TradeSerializers
    filter_backends = [DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['symbol', "is_open",'is_futuer']
    ordering_fields = '__all__'
    queryset = models.Trade.objects.all()
