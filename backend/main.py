from fastapi import FastAPI
from pymongo import MongoClient
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
import math

load_dotenv()
mongo_pwd = os.getenv("MONGO_PWD")

app = FastAPI()
client = MongoClient(f"mongodb+srv://JuneWay:{mongo_pwd}@ethanc.qgevd.mongodb.net/")
db = client['JobDB']
geo_db = client['GeoDB']
collection = db['jobs']
geo_collection = geo_db['geo_locations']
summary_collection = db['job_summary']

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def sanitize_document(doc):
    for key, value in doc.items():
        if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
            doc[key] = None
    return doc


@app.get('/')
def root():
    return {"mysterious man": "Welcome to the Job Data API landing page! Type '/api/jobs' to get the latest scraped job data!"}

@app.get('/api/jobs')
def get_jobs():
    jobs = list(collection.find({},{"_id": 0}))
    return jobs

@app.get("/api/geo_locations")
def get_geo_locations():
    raw_docs = list(geo_collection.find({}, {"_id": 0}))
    safe_docs = [sanitize_document(doc) for doc in raw_docs]
    return safe_docs

@app.get('/api/job_summaries')
def get_job_summaries():
    summaries = list(summary_collection.find({}, {"_id": 0}))
    return summaries