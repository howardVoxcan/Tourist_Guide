# 🗺️ Smart Tourist Guide — Django x Dialogflow Web App

Welcome to **Smart Tourist Guide**, a full-stack AI-powered web application built with Django and integrated with Dialogflow to help users discover and plan trips like never before.

This isn’t your average travel app. It combines real-world practicality with algorithmic intelligence, sentiment-aware recommendations, and voice/chat interfaces — designed for users who expect more than just static pages.

---

## 📌 Table of Contents

- [🔍 Why This Project?](#-why-this-project)
- [⚙️ Tech Stack](#-tech-stack)
- [✨ Features](#-features)
  - [Basic Features](#basic-features)
  - [Advanced Features](#advanced-features)
- [🚀 Run the App Locally](#-run-the-app-locally)

---

## 🔍 Why This Project?

Most web apps in this space stop at CRUD: manage hotels, view restaurants, store reviews. That’s fine — but let’s be honest, it gets boring.

We wanted to build something that:
- Pushes **beyond the database**.
- Is **scalable** and **modular**.
- Solves **real tourist needs** (trip planning, route optimization, Q&A).
- Integrates **AI + NLP** meaningfully.
- Offers a **smart voice/chat interface** — not just forms and clicks.

> Because if your travel guide doesn’t talk back to you in 2025… is it even smart?

---

## ⚙️ Tech Stack

| Layer        | Technology                       |
|--------------|----------------------------------|
| Backend      | Django, Python                   |
| Frontend     | HTML5, CSS3, JavaScript (vanilla)|
| Database     | PostgreSQL                       |
| AI/NLP       | scikit-learn, joblib, Dialogflow |
| External API | WeatherAPI, DistanceMatrixAPI    |
| Hosting      | Localhost / deploy-ready         |

---

## ✨ Features

### ✅ Basic Features

- **Homepage**: Clean, responsive landing page.
- **Location Explorer**: Browse tourist locations and view full details.
- **Weather Forecast**: Get 3-day forecasts from WeatherAPI for any city.

### 🚀 Advanced Features

#### 🧠 Smart Trip Planner

Plan a trip by selecting multiple locations, with:
- **Custom start/end points** (e.g., Hotel → Airport).
- **Shortest path optimization** using a simplified **Hamiltonian Path** algorithm.
- **Persisted trip path data** per user.

#### 💬 Auto Reply via Sentiment Analysis

If a location lacks user reviews, no problem:
- We use a trained **sentiment analysis model** (from `.ipynb → .pkl`) to auto-generate experience summaries.
- Real reviews override AI-generated ones — obviously.

#### 🤖 Chatbot Assistant

Powered by **Dialogflow**, our chatbot can:
- Answer FAQs about the system.
- Add/remove favorite locations.
- Trigger **trip creation** purely by chat or voice.
- Talk to you — because UX > UI.

#### 🛠 High Reusability

All chatbot intents/entities/knowledge bases are:
- **Script-generated from Python**.
- Uploadable via JSON/CSV.
- Easy to adapt to **any new city**, just swap the database.
A Python script named `importing.py` lets you generate the entire database automatically from a CSV file. You just need to prepare the CSV — it handles the rest.
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
