import csv
import os
import django
from datetime import datetime

# Thiết lập Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Tourist_Guide.settings")
django.setup()

from location.models import Location
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

# Step 1: Đọc toàn bộ file CSV và lưu vào bộ nhớ
csv_path = 'location_db.csv'
rows = []
long_descriptions = []

with open(csv_path, newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        rows.append(row)
        long_descriptions.append(row['Long Description'].strip())

# Step 2: Huấn luyện TF-IDF trên toàn bộ long_descriptions
vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)
tfidf_matrix = vectorizer.fit_transform(long_descriptions)
feature_names = vectorizer.get_feature_names_out()

# Hàm chuyển thời gian
def parse_time_field(time_str):
    if not time_str:
        return None
    time_str = time_str.strip()
    formats = ["%I:%M %p", "%H:%M", "%I:%M:%S %p", "%H:%M:%S"]
    for fmt in formats:
        try:
            return datetime.strptime(time_str, fmt).time()
        except ValueError:
            continue
    print(f"[CẢNH BÁO] Không thể parse thời gian: '{time_str}'")
    return None

# Step 3: Duyệt từng dòng, trích xuất top từ khóa và ghi vào DB
for idx, row in enumerate(rows):
    tfidf_scores = tfidf_matrix[idx].toarray().flatten()
    top_indices = tfidf_scores.argsort()[::-1][:10]
    tags = [feature_names[i] for i in top_indices if tfidf_scores[i] > 0]

    code = row['CODE'].strip()
    description = row['Description'].strip()
    long_description = row['Long Description'].strip()

    data = {
        'location': row['LOCATION'].strip(),
        'type': row['TYPE'].strip(),
        'rating': float(row['RATING (MAX = 5)']) if row['RATING (MAX = 5)'] else 5.0,
        'address': row['Address'].strip(),
        'description': description,
        'ticket_info': row['Ticket Info'].strip(),
        'image_path': row['image_path'].strip(),
        'coordinate': row['coordinate'].strip(),
        'long_description': long_description,
        'open_time': parse_time_field(row.get('open_time', '')),
        'close_time': parse_time_field(row.get('close_time', '')),
        'tags': tags,
    }

    obj, created = Location.objects.update_or_create(
        code=code,
        defaults=data
    )

    if created:
        print(f"✅ Đã tạo mới Location: {code}")
    else:
        print(f"🔄 Đã cập nhật Location: {code}")
