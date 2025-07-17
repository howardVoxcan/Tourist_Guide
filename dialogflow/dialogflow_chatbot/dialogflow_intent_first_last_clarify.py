import csv
import json

# Load locations from CSV
filename = "location_db_with_tags.csv"
locations = []

with open(filename, newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        location = row['LOCATION'].strip()
        locations.append(location)

# Templates with 1 placeholder
start_templates = [
    "Start from {}", "Begin at {}", "My first stop is {}",
    "The trip starts at {}", "I want to start at {}"
]

end_templates = [
    "End at {}", "Finish at {}", "My last stop is {}",
    "The trip ends at {}", "I want to end at {}"
]

# Function to generate userSays for ALL locations (no random sampling)
def generate_user_says(locations, templates):
    user_says = []

    for template in templates:
        prefix, suffix = template.split('{}')
        for loc in locations:
            user_says.append({
                "isTemplate": False,
                "count": 0,
                "updated": None,
                "data": [
                    {"text": prefix, "userDefined": False},
                    {
                        "text": loc,
                        "alias": "locations",
                        "meta": "@locations",
                        "userDefined": True
                    },
                    {"text": suffix, "userDefined": False}
                ],
                "id": ""
            })
    return user_says

# Intent generator
def create_intent(name, user_says, reply):
    return {
        "name": name,
        "auto": True,
        "responses": [
            {
                "messages": [
                    {
                        "type": "message",
                        "condition": "",
                        "speech": [reply]
                    }
                ],
                "parameters": [
                    {
                        "name": "locations",
                        "dataType": "@locations",
                        "value": "$locations",
                        "isList": False
                    }
                ]
            }
        ],
        "userSays": user_says
    }

# Create intents
start_user_says = generate_user_says(locations, start_templates)
end_user_says = generate_user_says(locations, end_templates)

start_intent = create_intent("set.start.location", start_user_says, "Got it. I’ve set the starting location.")
end_intent = create_intent("set.end.location", end_user_says, "Alright. I’ve set the ending location.")

# Save to JSON
with open("set.start.location.json", "w", encoding="utf-8") as f:
    json.dump(start_intent, f, indent=2, ensure_ascii=False)

with open("set.end.location.json", "w", encoding="utf-8") as f:
    json.dump(end_intent, f, indent=2, ensure_ascii=False)

print("✅ Generated: set.start.location.json and set.end.location.json")
