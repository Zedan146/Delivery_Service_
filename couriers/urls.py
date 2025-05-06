from django.urls import path
from . import views

app_name = 'couriers'
 
urlpatterns = [
    path('orders/', views.courier_orders, name='order_list'),
    path('orders/<int:pk>/', views.courier_order_detail, name='order_detail'),
    path('vehicles/', views.courier_vehicles, name='vehicle_list'),
] 