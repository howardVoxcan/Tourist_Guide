import csv
import os
import django

# Đặt settings module nếu chạy file này ngoài shell
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Tourist_Guide.settings")
django.setup()

from location.models import Location  # Đúng theo app 'location'

with open('location_db.csv', newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)

    for row in reader:
        code = row['CODE'].strip()

        data = {
            'location': row['LOCATION'].strip(),
            'city': row['CITY'].strip(),
            'type': row['TYPE'].strip(),
            'rating': float(row['RATING (MAX = 5)']) if row['RATING (MAX = 5)'] else 5.0,
            'address': row['Address'].strip(),
            'description': row['Description'].strip(),
            'ticket_info': row['Ticket Info'].strip(),
            'image_path': row['image_path'].strip(),
            'open_hours': row['open_hour'].strip(),
            'coordinate': row['coordinate'].strip(),
        }

        obj, created = Location.objects.update_or_create(
            code=code,
            defaults=data
        )

        if created:
            print(f"Đã tạo mới Location: {code}")
        else:
            print(f"Đã cập nhật Location: {code}")
