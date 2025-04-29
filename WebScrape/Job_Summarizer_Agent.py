from pymongo import MongoClient
from openai import OpenAI
from dotenv import load_dotenv
import os
from tqdm import tqdm

load_dotenv()
mongo_pwd = os.getenv("MONGO_PWD")
openai_api_key = os.getenv("OPENAI_API_KEY")

client = MongoClient(f"mongodb+srv://JuneWay:{mongo_pwd}@ethanc.qgevd.mongodb.net/")
db = client["JobDB"]
jobs_collection = db["jobs"]

from openai import OpenAI

client = OpenAI(api_key=openai_api_key)

def summarize_description(description):
    prompt = f"""
You're a summarizer agent that helps job seekers. 
Given a job description, do the following:
1. Write a 1–2 sentence summary.
2. List key skills required in a comma separated line.
3. List degree/education requirements in a comma separated line.

Job Description:
\"\"\"{description}\"\"\"

Respond in JSON with keys: summary, skills_desired, degree_qualifications.
"""
    response = client.chat.completions.create(model="gpt-4",
    messages=[{"role": "user", "content": prompt}],
    temperature=0.2)

    return eval(response.choices[0].message.content)

jobs = list(jobs_collection.find())
for job in tqdm(jobs):
    desc = job.get("job_description")
    if not desc:
        continue

    try:
        result = summarize_description(desc)
        jobs_collection.update_one(
            {"_id": job["_id"]},
            {"$set": {
                "summary": result.get("summary"),
                "skills_desired": result.get("skills_desired"),
                "degree_qualifications": result.get("degree_qualifications")
            }}
        )
    except Exception as e:
        print(f"Failed on job {job.get('job_title')}: {e}")
