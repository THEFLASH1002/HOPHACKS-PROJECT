from flask import Flask, request, jsonify, render_template
import requests
import os
import json
import random
import pandas as pd
from datetime import datetime, timedelta

app = Flask(__name__, static_folder="static", template_folder="templates")

# =========================
# OpenRouter API Chat Setup
# =========================
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_NAME = "google/gemini-2.0-flash-exp:free"

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_message = data.get("message", "")

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": user_message}],
        "temperature": 0.7,
        "max_tokens": 500,
    }

    try:
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        bot_reply = response.json()["choices"][0]["message"]["content"]
        return jsonify({"reply": bot_reply})
    except Exception as e:
        print("Chat API error:", e)
        return jsonify({"reply": "Something went wrong."}), 500


# =========================
# Hospital & Crime Data
# =========================
with open("data/hospitals.geojson", "r") as f:
    hospital_geojson = json.load(f)

for feature in hospital_geojson["features"]:
    props = feature["properties"]
    props["occupancy"] = random.randint(50, 100)

crime_df = pd.read_csv("data/crime.csv", parse_dates=["CrimeDateTime"])

def compute_crime_counts():
    cutoff = datetime.now() - timedelta(days=7)
    recent = crime_df[crime_df["CrimeDateTime"] >= cutoff]

    recent["Neighborhood_norm"] = (
        recent["Neighborhood"].astype(str).str.strip().str.lower()
    )
    counts = recent.groupby("Neighborhood_norm").size().to_dict()
    return counts

def compute_heat_scores():
    crime_counts = compute_crime_counts()

    with open("data/neighborhood.geojson", "r") as f:
        neighborhoods = json.load(f)

    for feature in neighborhoods["features"]:
        props = feature["properties"]
        name = props.get("Name") or props.get("Neighborhood") or "Unknown"
        name_norm = str(name).strip().lower()

        props["name"] = name
        props["crime_count"] = int(crime_counts.get(name_norm, 0))
        props["heat_score"] = random.randint(1, 100)

    return neighborhoods

def compute_hotspots():
    cutoff = datetime.now() - timedelta(days=7)
    recent = crime_df[crime_df["CrimeDateTime"] >= cutoff]

    features = []
    for _, row in recent.iterrows():
        lat, lon = row["Latitude"], row["Longitude"]
        if pd.notna(lat) and pd.notna(lon):
            features.append(
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [lon, lat],
                    },
                    "properties": {"intensity": random.randint(1, 100)},
                }
            )

    geojson = {"type": "FeatureCollection", "features": features}
    return geojson


# =========================
# API Routes
# =========================
@app.route("/api/hospitals")
def get_hospitals():
    return jsonify(hospital_geojson)

@app.route("/api/neighborhoods")
def get_neighborhoods():
    neighborhoods = compute_heat_scores()
    return jsonify(neighborhoods)

@app.route("/api/hotspots")
def get_hotspots():
    hotspots = compute_hotspots()
    return jsonify(hotspots)


# =========================
# Frontend Routes
# =========================
@app.route("/")
def index():
    return render_template("home.html")

@app.route("/home")
def home():
    return render_template("home.html")

@app.route("/map")
def map_page():
    return render_template("map.html")

@app.route("/dash")
def dash():
    return render_template("dash.html")


# =========================
# Run the App
# =========================
if __name__ == "__main__":
    app.run(debug=True)
