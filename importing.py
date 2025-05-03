import csv
import os
import django
from datetime import datetime

# Thiết lập Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Tourist_Guide.settings")
django.setup()

from location.models import Location  # Thay đúng tên app nếu khác

def parse_time_field(time_str):
    """Chuyển '8:00', '08:00 AM', '23:00' thành datetime.time object hoặc None."""
    if not time_str:
        return None
    time_str = time_str.strip()

    formats = ["%I:%M %p", "%H:%M", "%I:%M:%S %p", "%H:%M:%S"]  # hỗ trợ nhiều định dạng giờ

    for fmt in formats:
        try:
            return datetime.strptime(time_str, fmt).time()
        except ValueError:
            continue

    print(f"[CẢNH BÁO] Không thể parse thời gian: '{time_str}'")
    return None

with open('location_db.csv', newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)

    for row in reader:
        code = row['CODE'].strip()

        data = {
            'location': row['LOCATION'].strip(),
            'type': row['TYPE'].strip(),
            'rating': float(row['RATING (MAX = 5)']) if row['RATING (MAX = 5)'] else 5.0,
            'address': row['Address'].strip(),
            'description': row['Description'].strip(),
            'ticket_info': row['Ticket Info'].strip(),
            'image_path': row['image_path'].strip(),
            'coordinate': row['coordinate'].strip(),
            'long_description': row['Long Description'].strip(),
            'open_time': parse_time_field(row.get('open_time', '')),
            'close_time': parse_time_field(row.get('close_time', '')),
        }

        obj, created = Location.objects.update_or_create(
            code=code,
            defaults=data
        )

        if created:
            print(f"✅ Đã tạo mới Location: {code}")
        else:
            print(f"🔄 Đã cập nhật Location: {code}")
