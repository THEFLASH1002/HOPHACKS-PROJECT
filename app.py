from flask import Flask, render_template, jsonify
import pandas as pd
import json

app = Flask(__name__)

# Load and process neighborhoods + crime data
def compute_heat_scores():
    # Load crime data
    crime_df = pd.read_csv("data/crime.csv")

    # Normalize CSV neighborhood names
    crime_df["Neighborhood_norm"] = crime_df["Neighborhood"].str.strip().str.lower()

    # Count crimes by normalized neighborhood
    crime_counts = crime_df["Neighborhood_norm"].value_counts().to_dict()

    # Load GeoJSON neighborhoods
    with open("data/neighborhood.geojson", "r") as f:
        neighborhoods = json.load(f)

    # Attach crime counts
    for feature in neighborhoods["features"]:
        props = feature["properties"]

        # Get neighborhood name from GeoJSON
        name = props.get("Name") or props.get("Neighborhood") or "Unknown"
        name_norm = str(name).strip().lower()

        # Attach original + crime count
        props["name"] = name
        props["crime_count"] = int(crime_counts.get(name_norm, 0))

    return neighborhoods


@app.route("/")
def index():
    return render_template("map.html")


@app.route("/api/neighborhoods")
def get_neighborhoods():
    neighborhoods = compute_heat_scores()
    return jsonify(neighborhoods)


# Optional debug endpoint to see counts quickly
@app.route("/api/debug_counts")
def debug_counts():
    crime_df = pd.read_csv("data/crime.csv")
    return crime_df["Neighborhood"].value_counts().to_dict()


if __name__ == "__main__":
    app.run(debug=True)
