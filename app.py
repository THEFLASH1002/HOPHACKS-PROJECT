from flask import Flask, render_template, jsonify
import pandas as pd
import json
import random

app = Flask(__name__)

# Load hospital data (CSV)
hospitals = pd.read_csv("data/hospital.csv")

# Convert hospital coords to GeoJSON-like dict
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
            "occupancy": random.randint(50, 100)  # simulate hospital occupancy %
        }
    }
    for _, row in hospitals.iterrows()
]

# Load neighborhoods (GeoJSON as plain JSON)
with open("data/neighborhood.geojson", "r") as f:
    neighborhoods = json.load(f)

# Simulate EMS demand heat by neighborhood
for feature in neighborhoods["features"]:
    feature["properties"]["heat_score"] = random.randint(1, 100)


@app.route("/")
def index():
    return render_template("map.html")


@app.route("/api/hospitals")
def get_hospitals():
    return jsonify({
        "type": "FeatureCollection",
        "features": hospital_points
    })


@app.route("/api/neighborhoods")
def get_neighborhoods():
    return jsonify(neighborhoods)


if __name__ == "__main__":
    app.run(debug=True)
