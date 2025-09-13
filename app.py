from flask import Flask, request, jsonify, send_from_directory, render_template
import requests
import os
import pandas as pd
import json
import random

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
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "user", "content": user_message}
        ],
        "temperature": 0.7,
        "max_tokens": 500
    }

    try:
        response = requests.post(
            OPENROUTER_API_URL,
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        bot_reply = response.json()["choices"][0]["message"]["content"]
        return jsonify({"reply": bot_reply})
    except Exception as e:
        print(e)
        return jsonify({"reply": "Something went wrong."}), 500

# =========================
# Hospital & Neighborhood Data
# =========================
hospitals = pd.read_csv("data/hospital.csv")

hospital_points = [
    {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [row["X"] / 100000, row["Y"] / 100000]  # normalize scaling
        },
        "properties": {
            "name": row["name"],
            "address": row["address"],
            "city": row["city"],
            "state": row["state"],
            "zipcode": row["zipcode"],
            "occupancy": random.randint(50, 100)
        }
    }
    for _, row in hospitals.iterrows()
]

with open("data/neighborhood.geojson", "r") as f:
    neighborhoods = json.load(f)

for feature in neighborhoods["features"]:
    feature["properties"]["heat_score"] = random.randint(1, 100)

@app.route("/api/hospitals")
def get_hospitals():
    return jsonify({
        "type": "FeatureCollection",
        "features": hospital_points
    })

@app.route("/api/neighborhoods")
def get_neighborhoods():
    return jsonify(neighborhoods)

# =========================
# Frontend
# =========================
@app.route("/")
def index():
    return render_template("home.html")

# =========================
# Run the App
# =========================
if __name__ == "__main__":
    app.run(debug=True)
