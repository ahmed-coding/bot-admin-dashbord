from django.urls import path, include
from . import views
urlpatterns = [
    path('get-top/', views.SymbolView.as_view({'get': 'list'})),
    
    path('create-trade/', views.TradeView.as_view({'post': 'create'})),
    path('update-trade/<int:pk>/', views.TradeView.as_view({'put': 'partial_update', 'patch': 'partial_update'})),

    path('list-trade/', views.TradeView.as_view({'get': 'list'})),
    


]