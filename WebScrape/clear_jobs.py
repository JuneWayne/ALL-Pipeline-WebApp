from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()
mongo_pwd = os.getenv("MONGO_PWD")

client = MongoClient(f"mongodb+srv://JuneWay:{mongo_pwd}@ethanc.qgevd.mongodb.net/")
db = client["JobDB"]
db["jobs"].delete_many({})


print(" Cleared 'jobs_data' collection in JobDB.")

geo_db = client["GeoDB"]
geo_db["geo_locations"].delete_many({})

print(" Cleared 'geo_locations' collection in GeoDB.")

db['job_summary'].delete_many({})
print(" Cleared 'job_summary' collection in JobDB.")