from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('', views.order_list, name='order_list'),
    path('create/', views.order_create, name='order_create'),
    path('<int:pk>/', views.order_detail, name='order_detail'),
    path('<int:pk>/edit/', views.order_edit, name='order_edit'),
    path('<int:pk>/cancel/', views.order_cancel, name='order_cancel'),
    path('<int:pk>/assign-courier/', views.order_assign_courier, name='order_assign_courier'),
    path('<int:pk>/delete/', views.order_delete, name='order_delete'),
    path('orders/<int:pk>/receipt/', views.order_receipt_pdf, name='order_receipt'),
    path('clients/', views.client_list, name='client_list'),
    path('clients/create/', views.client_create, name='client_create'),
    path('clients/<int:pk>/', views.client_detail, name='client_detail'),
    path('clients/<int:pk>/edit/', views.client_edit, name='client_edit'),
    path('delivery-report/', views.delivery_report_pdf, name='delivery_report'),
    path('get-client-addresses/', views.get_client_addresses, name='get_client_addresses'),
] 