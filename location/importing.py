import csv
from location.models import Location

with open('location/database.csv', newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    objs = []
    for row in reader:
        objs.append(
            Location(
                code=row['ID'],  # Dùng 'code' thay vì 'id'
                location=row['LOCATION'],
                city=row['CITY'],
                type=row['TYPE'],
                rating=float(row['RATING']) if row['RATING'] else None,
                description=row['INTRODUCTION'] or ''
            )
        )
    
    Location.objects.bulk_create(objs)
    print(f"✅ Đã import {len(objs)} địa điểm thành công.")