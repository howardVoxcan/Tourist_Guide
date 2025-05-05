import csv
import os
import django
from datetime import datetime

# Thiết lập Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Tourist_Guide.settings")
django.setup()

from location.models import Location  # Thay đúng tên app nếu khác

# NLP Imports
import spacy
import nltk
from nltk.corpus import words

nltk.download('words')
nlp = spacy.load("en_core_web_sm")
english_vocab = set(w.lower() for w in words.words())

def extract_clean_english_tags(text):
    doc = nlp(text)
    tags = set()

    for token in doc:
        if token.pos_ in ("NOUN", "PROPN") and not token.is_stop:
            lemma = token.lemma_.lower()
            if lemma in english_vocab and len(lemma) > 1:
                tags.add(lemma)

    for ent in doc.ents:
        ent_text = ent.text.lower()
        if all(word in english_vocab for word in ent_text.split()):
            tags.add(ent_text)

    return list(tags)[:5]

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
        description = row['Description'].strip()
        long_description = row['Long Description'].strip()
        combined_text = f"{description} {long_description}"
        auto_tags = extract_clean_english_tags(combined_text)

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
            'tags': ','.join(auto_tags)
        }

        obj, created = Location.objects.update_or_create(
            code=code,
            defaults=data
        )

        if created:
            print(f"✅ Đã tạo mới Location: {code}")
        else:
            print(f"🔄 Đã cập nhật Location: {code}")
