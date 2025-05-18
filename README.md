# Django Delivery Management System

Система управления доставкой на базе Django, включающая управление заказами, курьерами, клиентами и транспортными средствами.

## Основные возможности

- Управление заказами (создание, отслеживание, печать чеков)
- Управление курьерами и их производительностью
- Управление транспортными средствами
- Система отчетности и аналитики
- Печать PDF-документов (чеки, отчеты)
- Оптимизированная производительность с использованием кэширования
- Валидация данных на уровне моделей

## Структура проекта

```
delivery_system/
├── clients/          # Управление клиентами
├── couriers/         # Управление курьерами
├── logistics/        # Логистика и транспорт
├── orders/          # Управление заказами
├── users/           # Пользователи и аутентификация
├── templates/       # Шаблоны
├── static/          # Статические файлы
└── media/           # Загружаемые файлы
```

## Технические особенности

- Django 5.2
- SQLite (для разработки)
- WeasyPrint для генерации PDF
- Оптимизированные запросы к БД
- Кэширование статусов транспортных средств
- Валидация данных на уровне моделей
- Индексация часто используемых полей

## Запуск проекта на Windows

### 1. Установка зависимостей Python

```bash
pip install -r requirements.txt
```

### 2. Установка GTK3 для WeasyPrint

WeasyPrint требует наличия внешних библиотек (GTK3, Cairo, Pango и др.), которые не устанавливаются через pip.

**Скачайте и установите GTK3 Runtime для Windows:**

- Перейдите по ссылке: [GTK3 for Windows Runtime Installer](https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases/tag/2022-01-04)
- Скачайте архив `gtk3-runtime-...-setup.exe` или `.zip`
- Установите или распакуйте архив, например, в `C:\GTK3`

**Добавьте путь к папке `bin` в переменную среды PATH:**

1. Откройте "Свойства системы" → "Переменные среды"
2. В переменную среды `PATH` добавьте путь к папке `bin` внутри установленного GTK3
3. Перезапустите терминал или IDE

### 3. Настройка базы данных

```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Создание суперпользователя (опционально)

```bash
python manage.py createsuperuser
```

### 5. Запуск сервера разработки

```bash
python manage.py runserver
```

## Разработка

### Создание тестовых данных

```bash
python create_test_data.py
```

## Дополнительная информация

- [Документация Django](https://docs.djangoproject.com/)
- [Документация WeasyPrint](https://weasyprint.readthedocs.io/)
- [Руководство по установке GTK3](https://weasyprint.readthedocs.io/en/stable/install.html#windows)

---

**Примечание:** Без установки GTK3 PDF-функционал работать не будет!

Подробнее: [WeasyPrint Windows install](https://weasyprint.readthedocs.io/en/stable/install.html#windows) 
