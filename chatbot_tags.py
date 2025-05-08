import pandas as pd

# Replace this with your actual source CSV or database query result
input_file = "all_locations.csv"  # Your full data with LOCATION and tags
output_file = "locations_with_tags.csv"

# Load the dataset
df = pd.read_csv("location_db_with_tags.csv")

# Ensure column names match exactly
if not {"LOCATION", "tags"}.issubset(df.columns):
    raise ValueError("CSV must contain 'LOCATION' and 'tags' columns.")

# Select only the necessary columns
df_subset = df[["LOCATION", "tags"]].copy()

# Optional: Clean up whitespace and ensure proper formatting
df_subset["LOCATION"] = df_subset["LOCATION"].str.strip()
df_subset["tags"] = df_subset["tags"].apply(lambda x: ",".join(tag.strip() for tag in str(x).split(",")))

# Save to new CSV
df_subset.to_csv(output_file, index=False, quoting=1)  # quoting=1 means quote all fields (csv.QUOTE_ALL)

print(f"Saved cleaned CSV to: {output_file}")
