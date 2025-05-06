import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'delivery_system.settings')
django.setup()

from django.contrib.auth import get_user_model
from orders.models import Client, Order
from logistics.models import Vehicle, CourierVehicle
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

def create_test_users():
    # Создаем логиста
    logistician = User.objects.create_user(
        username='logistician',
        password='logistician123',
        email='logistician@example.com',
        first_name='Иван',
        last_name='Логистов',
        role='LOGISTICIAN',
        phone_number='+7 (999) 123-45-67',
        address='г. Москва, ул. Логистическая, д. 1'
    )
    
    # Создаем курьеров
    courier1 = User.objects.create_user(
        username='courier1',
        password='courier123',
        email='courier1@example.com',
        first_name='Петр',
        last_name='Курьеров',
        role='COURIER',
        phone_number='+7 (999) 234-56-78',
        address='г. Москва, ул. Курьерская, д. 1'
    )
    
    courier2 = User.objects.create_user(
        username='courier2',
        password='courier123',
        email='courier2@example.com',
        first_name='Анна',
        last_name='Курьерова',
        role='COURIER',
        phone_number='+7 (999) 345-67-89',
        address='г. Москва, ул. Курьерская, д. 2'
    )
    
    return logistician, courier1, courier2

def create_test_vehicles():
    # Создаем транспортные средства
    bicycle = Vehicle.objects.create(
        type='BICYCLE',
        model='Stels Navigator-500',
        color='Красный',
        plate_number='',
        description='Горный велосипед, 21 скорость',
        is_active=True
    )
    
    motorcycle = Vehicle.objects.create(
        type='MOTORCYCLE',
        model='Honda CBR 600RR',
        color='Черный',
        plate_number='A123BC',
        description='Спортивный мотоцикл',
        is_active=True
    )
    
    car = Vehicle.objects.create(
        type='CAR',
        model='Toyota Corolla',
        color='Белый',
        plate_number='E456KM',
        description='Седан, 1.6L',
        is_active=True
    )
    
    return bicycle, motorcycle, car

def create_test_clients():
    # Создаем клиентов
    client1 = Client.objects.create(
        first_name='Алексей',
        last_name='Иванов',
        middle_name='Петрович',
        phone_number='+7 (999) 111-22-33',
        email='ivanov@example.com',
        address='г. Москва, ул. Ленина, д. 10, кв. 5'
    )
    
    client2 = Client.objects.create(
        first_name='Мария',
        last_name='Сидорова',
        middle_name='Ивановна',
        phone_number='+7 (999) 444-55-66',
        email='sidorova@example.com',
        address='г. Москва, пр. Мира, д. 20, кв. 15'
    )
    
    return client1, client2

def create_test_orders(clients, couriers):
    # Создаем заказы
    orders = []
    
    # Новый заказ
    order1 = Order.objects.create(
        order_number='ORD-001',
        client=clients[0],
        delivery_address='г. Москва, ул. Ленина, д. 10, кв. 5',
        order_amount=Decimal('1500.00'),
        delivery_date=timezone.now().date() + timedelta(days=1),
        status='NEW'
    )
    orders.append(order1)
    
    # Назначенный заказ
    order2 = Order.objects.create(
        order_number='ORD-002',
        client=clients[1],
        courier=couriers[0],
        delivery_address='г. Москва, пр. Мира, д. 20, кв. 15',
        order_amount=Decimal('2500.00'),
        delivery_date=timezone.now().date() + timedelta(days=2),
        status='ASSIGNED'
    )
    orders.append(order2)
    
    # Заказ в процессе
    order3 = Order.objects.create(
        order_number='ORD-003',
        client=clients[0],
        courier=couriers[1],
        delivery_address='г. Москва, ул. Ленина, д. 10, кв. 5',
        order_amount=Decimal('3500.00'),
        delivery_date=timezone.now().date(),
        status='IN_PROGRESS'
    )
    orders.append(order3)
    
    return orders

def create_test_courier_vehicles(couriers, vehicles):
    # Назначаем транспортные средства курьерам
    CourierVehicle.objects.create(
        courier=couriers[0],
        vehicle=vehicles[0],  # Велосипед
        is_current=True
    )
    
    CourierVehicle.objects.create(
        courier=couriers[1],
        vehicle=vehicles[1],  # Мотоцикл
        is_current=True
    )

def main():
    print("Создание тестовых данных...")
    
    # Создаем пользователей
    logistician, courier1, courier2 = create_test_users()
    print("Созданы пользователи")
    
    # Создаем транспортные средства
    bicycle, motorcycle, car = create_test_vehicles()
    print("Созданы транспортные средства")
    
    # Создаем клиентов
    client1, client2 = create_test_clients()
    print("Созданы клиенты")
    
    # Создаем заказы
    orders = create_test_orders([client1, client2], [courier1, courier2])
    print("Созданы заказы")
    
    # Назначаем транспортные средства курьерам
    create_test_courier_vehicles([courier1, courier2], [bicycle, motorcycle])
    print("Назначены транспортные средства курьерам")
    
    print("\nТестовые данные успешно созданы!")
    print("\nДанные для входа:")
    print("Администратор:")
    print("Логин: admin")
    print("Пароль: (тот, который вы указали при создании)")
    print("\nЛогист:")
    print("Логин: logistician")
    print("Пароль: logistician123")
    print("\nКурьеры:")
    print("Логин: courier1")
    print("Пароль: courier123")
    print("Логин: courier2")
    print("Пароль: courier123")

if __name__ == '__main__':
    main() 