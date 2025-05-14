from django.urls import path
from . import views

app_name = 'logistics'

urlpatterns = [
    path('vehicles/', views.vehicle_list, name='vehicle_list'),
    path('vehicles/create/', views.vehicle_create, name='vehicle_create'),
    path('vehicles/<int:pk>/', views.vehicle_detail, name='vehicle_detail'),
    path('vehicles/<int:pk>/edit/', views.vehicle_edit, name='vehicle_edit'),
    path('courier-vehicles/', views.courier_vehicle_list, name='courier_vehicle_list'),
    path('courier-vehicles/assign/', views.courier_vehicle_assign, name='courier_vehicle_assign'),
    path('courier-vehicles/<int:pk>/unassign/', views.courier_vehicle_unassign, name='courier_vehicle_unassign'),
    path('reports/', views.delivery_report_list, name='delivery_report_list'),
    path('reports/<int:pk>/', views.delivery_report_detail, name='delivery_report_detail'),
    path('performance/', views.courier_performance_list, name='courier_performance_list'),
    path('performance/<int:courier_id>/', views.courier_performance_detail, name='courier_performance_detail'),
] 