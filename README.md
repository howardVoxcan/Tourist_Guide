# 🗺️ Smart Tourist Guide — Django x Dialogflow Web App

Welcome to **Smart Tourist Guide**, a full-stack AI-powered web application built with Django and integrated with Dialogflow — designed to help users discover, plan, and optimize trips like never before.

This isn’t your average travel app. It blends real-world usefulness with intelligent automation, sentiment-aware recommendations, and natural conversation interfaces. The goal: a truly **smart** tourist assistant that feels personal, responsive, and actually helpful.

---

## 🔍 Why This Project?

Most travel apps today are just interactive catalogs — static listings of places, reviews, and maps. We wanted to go further by building something that:

- Goes beyond CRUD and static pages  
- Helps tourists **plan optimized routes**  
- Understands places through **tags and sentiment**, even without existing user input  
- Supports **voice and chat interaction** using Dialogflow  

Because in 2025, a tourist guide should do more than just show pins on a map.

---

## 🧠 Data Processing & NLP Intelligence

To build a truly smart system, we collected and processed **two separate datasets**, each serving a distinct NLP role:

---

### 📍 1. Place Data — Crawled + Tagged

We scraped detailed information for tourist locations (e.g., **name, address, category, coordinates, rating, description**) from sources like TripAdvisor and Google.

#### 🏷️ Tag Extraction (TF-IDF + SpaCy)

To enrich the description of each location:

- Applied **TfidfVectorizer** to extract **keywords** from the description field.  
- Used **SpaCy** (`en_core_web_sm`) for POS tagging and noun phrase extraction to identify relevant **semantic tags** like `"food"`, `"cafe"`, or `"metro"`.  
- Tags were stored in the database and made available for search, chatbot suggestions, and filtering.

This tagging approach simulates user-generated content for places that lack community input.

---

### 😊 2. Sentiment Analysis — Independent Review Dataset

In parallel, we developed a sentiment analysis module to generate experience summaries for each location.

#### 📦 Dataset

- Used an **review dataset** labeled as **positive**, **neutral**, or **negative**.
- This dataset is separate from crawled place data to maintain generalization.
- Text was preprocessed (lowercased, cleaned, etc.) and class imbalance was handled explicitly.

#### ⚙️ Model Training Pipeline

- Encoded labels using `LabelEncoder`.
- Transformed text using **TfidfVectorizer**.
- Calculated class weights using `compute_class_weight` to balance uneven class distribution.
- Trained a **XGBoost classifier** (`XGBClassifier`) with 5-fold cross-validation (`KFold`) to ensure robust evaluation.
- Saved the trained model using `joblib` and deployed it into the Django backend for live predictions.

#### 🧠 Use in the App

- When a location lacks real user reviews, the app auto-generates a short experience summary using the sentiment classifier.
- As user reviews accumulate, these AI-generated texts are replaced with real feedback.

---

## ✨ Key Features

### ✅ Basic

- Clean, mobile-friendly homepage and UI  
- Explore locations with full detail view and live 3-day weather forecast  
- Save favorite locations and manage personalized trip lists  

---

### 🚀 Advanced

#### 🗺 Smart Trip Planner

- Plan multi-stop trips with custom **start and end points**
- Route optimized via a simplified **Hamiltonian Path algorithm**
- Trip paths are saved to user history

#### 💬 Sentiment-Aware Review Generator

- Auto-generates experience summaries for places with no reviews  
- Replaced by real reviews when available  

#### 🤖 Dialogflow Chatbot Assistant

- Natural voice/chat interface for:
  - Answering FAQs
  - Adding/removing favorite locations
  - Creating entire trips via chat
- Intents and entities managed via Python scripts and importable JSON

---

## ⚙️ Smart Automation

### 📥 Auto Data Import

- `importing.py`: A one-command script that takes a formatted CSV and:
  - Parses each entry (e.g., name, rating, coordinates)
  - Applies TF-IDF and NLP to extract semantic tags
  - Automatically inserts all enriched data into SQLite

---

## 🧩 Designed for Extensibility

The system is highly modular:

- Want to expand to another city? Just update the CSV and re-run `importing.py`.
- Want to switch languages or retrain the sentiment model? Plug in a new dataset.
- Dialogflow agent can be updated by uploading new `intents.json` and `entities.json`.

---

## 🚀 Run the App Locally

```bash
# Clone the repo
git clone https://github.com/howardVoxcan/smart-tourist-guide.git
cd smart-tourist-guide

# Create virtual environment
python -m venv venv
source venv/bin/activate   # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Migrate DB & run
python manage.py migrate
python manage.py runserver
```
