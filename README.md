# Django Delivery Management System

## Запуск проекта на Windows

Для корректной работы печати PDF (WeasyPrint) требуется установить дополнительные библиотеки GTK3.

### 1. Установка зависимостей Python

```bash
pip install -r requirements.txt
```

### 2. Установка GTK3 для WeasyPrint

WeasyPrint требует наличия внешних библиотек (GTK3, Cairo, Pango и др.), которые не устанавливаются через pip.

**Скачайте и установите GTK3 Runtime для Windows:**

- Перейдите по ссылке: [GTK3 for Windows Runtime Installer](https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases/tag/2022-01-04)
- Скачайте архив `gtk3-runtime-...-setup.exe` или `.zip` (например, `gtk3-runtime-3.24.30-2021-01-04-ts-win64.zip`).
- Установите или распакуйте архив, например, в `C:\GTK3`.

**Добавьте путь к папке `bin` в переменную среды PATH:**

1. Откройте "Свойства системы" → "Переменные среды".
2. В переменную среды `PATH` добавьте путь к папке `bin` внутри установленного GTK3 (например, `C:\GTK3\bin`).
3. Перезапустите терминал или IDE.

### 3. Запуск проекта

```bash
python manage.py migrate
python manage.py runserver
```

---

**Без установки GTK3 PDF-функционал работать не будет!**

Подробнее: [WeasyPrint Windows install](https://weasyprint.readthedocs.io/en/stable/install.html#windows) 