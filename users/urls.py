from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('couriers/', views.courier_list, name='courier_list'),
    path('couriers/<int:pk>/', views.courier_detail, name='courier_detail'),
    path('couriers/print/', views.courier_report_pdf, name='courier_report'),
    path('logisticians/', views.logistician_list, name='logistician_list'),
    path('staff/create/', views.staff_create, name='staff_create'),
] 