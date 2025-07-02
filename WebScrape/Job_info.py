import pandas as pd
from pymongo import MongoClient
from dotenv import load_dotenv
import os
from collections import defaultdict
import statistics
import re

load_dotenv()

mongo_pwd = os.getenv("MONGO_PWD")
mongo_uri = f"mongodb+srv://JuneWay:{mongo_pwd}@ethanc.qgevd.mongodb.net/"

client = MongoClient(mongo_uri)
db = client["JobDB"]

jobs_collection = db["jobs"]
summaries_collection = db["job_summary"]

jobs = list(jobs_collection.find())

location_to_applicants = defaultdict(list)
for job in jobs:
    location = job.get('location', "").strip().lower()
    applicants_str = job.get('num_applicants')
    num_applicants = None

    if applicants_str:
        match = re.search(r'\d+', applicants_str)
        if match:
            num_applicants = int(match.group())

    if location and num_applicants is not None:
        location_to_applicants[location].append(num_applicants)

summary_docs = []

for location, applicants_list in location_to_applicants.items():
    summary = {
        'location': location,
        'number_of_jobs': len(applicants_list),
        'average_applicants': statistics.mean(applicants_list) if applicants_list else 0

    }
    summary_docs.append(summary)
summaries_collection.delete_many({})
if summary_docs:
    summaries_collection.insert_many(summary_docs)

print(f"Inserted {len(summary_docs)} summary documents into JobDB.job_summary")
