import pandas as pd
import requests
import time
from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()
mongo_pwd = os.getenv("MONGO_PWD")

client = MongoClient(f"mongodb+srv://JuneWay:{mongo_pwd}@ethanc.qgevd.mongodb.net/")
geo_db = client['GeoDB']
collection = geo_db['geo_locations']

csv_file = "Data_Science_Internship_Full.csv"
output_json = "locations_US.json"

def geocode(location_name):
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": f"{location_name}, United States",
        "format": "json",
        "limit": 1
    }
    response = requests.get(url, params=params, headers={"User-Agent": "USMapBot/1.0"})
    data = response.json()
    if data:
        return float(data[0]["lat"]), float(data[0]["lon"])
    return None, None

df = pd.read_csv(csv_file)

output = {}
geo_docs = []

for _, row in df.iterrows():
    loc_name = row["location"]
    print(f"Geocoding {loc_name}...")
    lat, lon = geocode(loc_name)
    time.sleep(1)
    if lat and lon:
        geo_doc = {
            "location": loc_name,
            "latitude": lat,
            "longitude": lon
        }
        geo_docs.append(geo_doc)
        output[loc_name] = {"lat": lat, "lng": lon}
    else:
        print(f"Could not geocode: {loc_name}")


collection.delete_many({}) 
if geo_docs:
    collection.insert_many(geo_docs)
    print(f" Inserted {len(geo_docs)} geo documents into GeoDB.geo_jobs")
else:
    print("No geo data to upload.")
