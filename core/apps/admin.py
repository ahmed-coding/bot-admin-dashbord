from django.contrib import admin
from . import models
# Register your models here.


class SymbolAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'trades', 'return_value','win_rate')
    search_fields = ['symbol',]
    list_filter = ['trades', 'win_rate']
    date_hierarchy = 'created_time'


admin.site.register(models.Symbol, SymbolAdmin)

class FSymbolAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'trades', 'return_value','win_rate')
    search_fields = ['symbol',]
    list_filter = ['trades', 'win_rate']
    date_hierarchy = 'created_time'


admin.site.register(models.FSymbol, FSymbolAdmin)


class TradeAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'is_open','is_futuer')
    search_fields = ['symbol',]
    list_filter = ['symbol', 'is_open','is_futuer']
    date_hierarchy = 'created_time'


admin.site.register(models.Trade, TradeAdmin)