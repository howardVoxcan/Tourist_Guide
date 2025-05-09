import pandas as pd
import spacy

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# Function to clean text
def clean_spacy(doc):
    tokens = [token.lemma_.lower().strip() for token in doc if not token.is_stop and not token.is_punct]
    return " ".join(tokens)

# Load CSV
df = pd.read_csv("reviews_dataset.csv")

# Preprocess review text
texts = df['review_full'].astype(str).tolist()
clean_texts = []
for doc in nlp.pipe(texts, disable=["ner", "parser"]):
    clean_texts.append(clean_spacy(doc))

df['clean_text'] = clean_texts

# Drop rows with missing values
df = df.dropna(subset=['clean_text', 'rating_review'])

# Assign sentiment labels
def assign_sentiment(rating):
    if rating >= 4:
        return 'positive'
    elif rating == 3:
        return 'neutral'
    else:
        return 'negative'

df['sentiment'] = df['rating_review'].apply(assign_sentiment)

# Save to new CSV
df.to_csv("preprocessed_reviews.csv", index=False)
print("✅ Preprocessing complete. File saved as 'preprocessed_reviews.csv'")
