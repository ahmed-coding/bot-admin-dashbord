from rest_framework import serializers
from . import models


class SymbolSerializers(serializers.ModelSerializer):
    
    
    class Meta:
        model= models.Symbol
        fields= '__all__'
        
        


class TradeSerializers(serializers.ModelSerializer):
    # is_open = serializers.ReadOnlyField()
    class Meta:
        model= models.Trade
        fields= '__all__'


