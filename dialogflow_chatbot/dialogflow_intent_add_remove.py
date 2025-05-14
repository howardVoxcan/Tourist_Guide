import csv
import json
import random
import itertools

# Load CSV
filename = "location_db_with_tags.csv"
locations = []

with open(filename, newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        location = row['LOCATION'].strip()
        locations.append(location)

# Templates for add/remove actions
add_templates = [
    "Add {}",
    "Can you add {}?",
    "I want to add {}",
    "Please include {}",
    "Put {} in my list",
    "Add {} and {}",
    "Please add both {} and {}",
    "Include {} and {} in my list",
    "I want to add {} as well as {}",
    "Add {} along with {}",
    "Put {} and {} in the list",
    "Could you add {} and also {}?",
]

remove_templates = [
    "Remove {}",
    "Can you remove {}?",
    "I want to remove {}",
    "Please delete {}",
    "Remove {} and {}",
    "Can you remove {} and {}?",
    "Please delete {} and {}",
    "I want to remove both {} and {}",
]

# Function to generate training phrases
def generate_action_phrases(locations, templates, action_name):
    user_says = []
    entity_name = "locations"
    sample_size = max(1, int(len(locations) * 0.1))  # 10% sample

    sampled = random.sample(locations, sample_size)
    paired = list(itertools.combinations(sampled, 2))[:max(1, sample_size // 2)]

    for template in templates:
        placeholder_count = template.count('{}')

        if placeholder_count == 2:
            for a, b in paired:
                parts = template.split('{}')
                if len(parts) == 3:
                    user_says.append({
                        "isTemplate": False,
                        "count": 0,
                        "updated": None,
                        "data": [
                            {"text": parts[0], "userDefined": False},
                            {"text": a, "alias": entity_name, "meta": f"@{entity_name}", "userDefined": True},
                            {"text": parts[1], "userDefined": False},
                            {"text": b, "alias": entity_name, "meta": f"@{entity_name}", "userDefined": True},
                            {"text": parts[2], "userDefined": False}
                        ],
                        "id": ""
                    })
                else:
                    print(f"Skipping invalid template (wrong split): {template}")

        elif placeholder_count == 1:
            for loc in sampled:
                try:
                    parts = template.split('{}')
                    if len(parts) == 2:
                        user_says.append({
                            "isTemplate": False,
                            "count": 0,
                            "updated": None,
                            "data": [
                                {"text": parts[0], "userDefined": False},
                                {"text": loc, "alias": entity_name, "meta": f"@{entity_name}", "userDefined": True},
                                {"text": parts[1], "userDefined": False}
                            ],
                            "id": ""
                        })
                    else:
                        print(f"Skipping invalid template (wrong split): {template}")
                except IndexError:
                    print(f"Skipping invalid template: {template}")
        else:
            print(f"Skipping invalid template (unsupported placeholder count): {template}")

    return user_says

# Intent for adding
add_user_says = generate_action_phrases(locations, add_templates, "add")
add_intent = {
    "name": "add.location",
    "auto": True,
    "responses": [
        {
            "messages": [
                {
                    "type": "message",
                    "condition": "",
                    "speech": ["Okay, I've added the location(s) to your list."]
                }
            ],
            "parameters": [
                {
                    "name": "location",
                    "dataType": "@locations",
                    "value": "$location",
                    "isList": True
                }
            ]
        }
    ],
    "userSays": add_user_says
}

# Intent for removing
remove_user_says = generate_action_phrases(locations, remove_templates, "remove")
remove_intent = {
    "name": "remove.location",
    "auto": True,
    "responses": [
        {
            "messages": [
                {
                    "type": "message",
                    "condition": "",
                    "speech": ["Got it. I've removed the location(s)."]
                }
            ],
            "parameters": [
                {
                    "name": "location",
                    "dataType": "@locations",
                    "value": "$location",
                    "isList": True
                }
            ]
        }
    ],
    "userSays": remove_user_says
}

# Save to JSON files
with open("trip.create.add.location.json", "w", encoding="utf-8") as f:
    json.dump(add_intent, f, indent=2, ensure_ascii=False)

with open("trip.create.remove.location.json", "w", encoding="utf-8") as f:
    json.dump(remove_intent, f, indent=2, ensure_ascii=False)

with open("favourite.add.location.json", "w", encoding="utf-8") as f:
    json.dump(add_intent, f, indent=2, ensure_ascii=False)

with open("favourite.remove.location.json", "w", encoding="utf-8") as f:
    json.dump(remove_intent, f, indent=2, ensure_ascii=False)

print("✅ Add and Remove intent files created successfully.")
