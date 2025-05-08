import csv
import json
import random

# Templates to generate user phrases
phrase_templates = [
    "I want to find {}",
    "I'm looking for {}",
    "Can you show me {}?",
    "Where is {}?",
    "Find {} for me",
    "I want to look for {}"  # Added this template
]

# Load CSV
filename = "location_db_with_tags.csv"
locations = []
tag_set = set()

with open(filename, newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        location = row['LOCATION'].strip()
        tags = [tag.strip() for tag in row['tags'].split(',')]
        locations.append({'location': location, 'tags': tags})
        tag_set.update(tags)

# Helper to create userSays entries
def make_user_says(entries, entity_name):
    user_says = []
    total_entries = len(entries)
    sample_size = max(1, int(total_entries * 0.1))  # 10% of the data, at least 1 entry
    
    # Randomly select 10% of the entries
    sampled_entries = random.sample(entries, sample_size)
    
    for entry in sampled_entries:
        for template in phrase_templates:
            phrase = template.format(entry)
            user_says.append({
                "isTemplate": False,  # No template, use directly as user input
                "count": 0,
                "updated": None,
                "data": [
                    {
                        "text": phrase.replace(entry, ""),
                        "userDefined": False
                    },
                    {
                        "text": entry,
                        "alias": entity_name,
                        "meta": f"@{entity_name}",  # Ensures entity extraction
                        "userDefined": True
                    }
                ],
                "id": ""
            })
    return user_says

# Ensure that every tag appears at least once
def ensure_tags_in_user_says(tag_set, entity_name):
    user_says = []
    for tag in tag_set:
        for template in phrase_templates:
            phrase = template.format(tag)
            user_says.append({
                "isTemplate": False,
                "count": 0,
                "updated": None,
                "data": [
                    {
                        "text": phrase.replace(tag, ""),
                        "userDefined": False
                    },
                    {
                        "text": tag,
                        "alias": entity_name,
                        "meta": f"@{entity_name}",
                        "userDefined": True
                    }
                ],
                "id": ""
            })
    return user_says

# Generate JSON for specific location intent
location_user_says = make_user_says([loc['location'] for loc in locations], "locations")
location_intent = {
    "name": "find.location.particular",
    "auto": True,
    "responses": [
        {
            "messages": [
                {
                    "type": "message",
                    "condition": "",
                    "speech": ["Sure, here is what I found for that location."]
                }
            ],
            "parameters": [
                {
                    "name": "location",
                    "dataType": "@locations",  # Ensure this is the correct Dialogflow entity
                    "value": "$location",
                    "isList": False
                }
            ]
        }
    ],
    "userSays": location_user_says
}

# Ensure that tags (like 'metro') are included at least once
tag_user_says = ensure_tags_in_user_says(tag_set, "tags")
tag_intent = {
    "name": "find.location.tags",
    "auto": True,
    "responses": [
        {
            "messages": [
                {
                    "type": "message",
                    "condition": "",
                    "speech": ["Here are some places matching that type."]
                }
            ],
            "parameters": [
                {
                    "name": "tag",
                    "dataType": "@tags",  # Ensure this is the correct Dialogflow entity
                    "value": "$tag",
                    "isList": False
                }
            ]
        }
    ],
    "userSays": tag_user_says
}

# --- Write to files ---
with open("find.location.particular.json", "w", encoding="utf-8") as f:
    json.dump(location_intent, f, indent=2, ensure_ascii=False)

with open("find.location.tags.json", "w", encoding="utf-8") as f:
    json.dump(tag_intent, f, indent=2, ensure_ascii=False)

print("Intent files created successfully.")
