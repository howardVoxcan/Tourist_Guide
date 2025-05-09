import csv
import re

# List of location names
locations = [
    "The Hammock Hotel Fine Arts Museum", "New World Saigon Hotel", "Brand New Cozy Home at the heart of SG",
    "Loan Vo Hostel", "Rex Hotel", "Hotel Majestic Saigon", "Lotte Hotel Saigon", "Fusion Suites Saigon",
    "ibis Saigon Airport", "The Airport Hotel", "TTC Hotel - Airport", "Suoi Tien Theme Park", "Dam Sen Park",
    "Amazing Bay", "Nguyen Hue Walking Street", "Landmark 81", "23/9 Park", "Saigon River Tour", "Snow Town Saigon",
    "Vietopia", "tiNiWorld", "HCMC Opera House (HBSO)", "Chill Sky Bar", "Bui Vien Street", "Club V E-Gaming",
    "Monte-Carlo Saigon", "Pho 2000", "Nha Hang Ngon", "Banh Mi Huynh Hoa", "The Workshop Coffee",
    "Café de Saigon1982", "Bun Rieu Ganh", "Bun Rieu Nguyen Canh Chan", "Singapore Frog Porridge Tan Dinh",
    "Banh Mi Bui Thi Xuan", "Dim Tu Tac", "Quince Saigon", "Kappou Nishiyama", "Pho Phu Vuong", "Xoi Ga Number One",
    "Kabin", "Lagom Café - Belgian Beer & Coffee Lounge", "Pho Bo Phu Gia", "Bo Kho Ganh",
    "Ho Chi Minh City Post Office", "Tao Dan Park", "Book Street", "Notre-Dame Cathedral Basilica of Saigon",
    "Nha Rong Wharf", "Independence Palace", "Saigon Zoo and Botanical Gardens", "Museum of Vietnamese History",
    "Cu Chi Tunnels", "Ba Thien Hau Temple", "Jade Emperor Pagoda", "Ba Chieu Market", "Ben Thanh Market",
    "Aeon Mall", "Takashimaya Vietnam", "Diamond Plaza", "Saigon Square", "The Cafe Apartments",
    "Big C Hoang Van Thu", "Tan Dinh Market", "Ben Thanh Market", "Tan Son Nhat International Airport",
    "Saigon Railway Station", "Mien Dong Bus Station", "Mien Tay Bus Station", "An Suong Bus Station",
    "Ben Thanh Bus Hub", "Cho Lon Bus Station", "Ben Thanh Metro Station", "Suoi Tien Metro Station"
]

# Abbreviation map
abbrev_map = {
    "hotel": ["htl", "hotl", "hoetl"],
    "saigon": ["sg", "saigon", "sai gon", "sai-gon"],
    "airport": ["airprt", "airpt", "arpt"],
    "street": ["st", "strt", "st."],
    "restaurant": ["resto", "restaurent", "rest"],
    "market": ["mkt", "mrkt"],
    "park": ["pk", "prak"],
    "station": ["stn", "sta", "statn"],
    "metro": ["subway", "underground"],
    "café": ["cafe", "coffe", "coffé"],
    "museum": ["musuem", "muzeum"],
    "pagoda": ["pogoda", "pagdoa"],
    "temple": ["templ", "tempel"]
}

# Strip accents manually
def strip_accents(text):
    replacements = {
        "àáâãäå": "a", "èéêë": "e", "ìíîï": "i", "òóôõö": "o", "ùúûü": "u",
        "ýÿ": "y", "ç": "c", "ñ": "n", "đ": "d", "ÀÁÂÃÄÅ": "A", "ÈÉÊË": "E",
        "ÌÍÎÏ": "I", "ÒÓÔÕÖ": "O", "ÙÚÛÜ": "U", "Ý": "Y", "Ç": "C", "Ñ": "N", "Đ": "D"
    }
    for accented, replacement in replacements.items():
        text = re.sub(f"[{accented}]", replacement, text)
    return text

# Generate synonyms
def generate_synonyms(name):
    base = name.lower()
    base_unaccented = strip_accents(base)
    synonyms = set([base, base_unaccented])
    for key, variations in abbrev_map.items():
        if key in base:
            for v in variations:
                synonyms.add(base.replace(key, v))
                synonyms.add(base_unaccented.replace(key, v))
    return list(synonyms)

# Write to CSV with double quotes
with open("dialogflow_locations_extended.csv", mode="w", newline='', encoding="utf-8") as file:
    writer = csv.writer(file, quoting=csv.QUOTE_ALL)
    writer.writerow(["value", "synonym"])
    for loc in locations:
        for synonym in generate_synonyms(loc):
            writer.writerow([loc, synonym])

print("CSV generated: dialogflow_locations_extended.csv")
