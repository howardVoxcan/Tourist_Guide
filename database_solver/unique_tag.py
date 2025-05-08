import csv

# Create an empty set to store unique tags
unique_tags = set()

# Open and read the CSV file
with open('locations_with_tags.csv', newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)  # Assuming the CSV has headers
    for row in reader:
        tags = row['tags']  # Replace 'tag' with the actual column name in your CSV
        tag_list = tags.split(',')  # Assuming tags are separated by commas, adjust if needed
        # Add each tag to the set (duplicates will be ignored)
        for tag in tag_list:
            unique_tags.add(tag.strip())  # Strip spaces if necessary

# Write unique tags to a txt file
with open('unique_tags.txt', 'w', encoding='utf-8') as f:
    for tag in unique_tags:
        f.write(f"{tag}\n")

print("Unique tags have been written to 'unique_tags.txt'")
