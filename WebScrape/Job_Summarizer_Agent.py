from pymongo import MongoClient
from openai import OpenAI
from dotenv import load_dotenv
import os, json
from tqdm import tqdm



load_dotenv()
mongo_pwd = os.getenv("MONGO_PWD")
openai_api_key = os.getenv("OPENAI_API_KEY")

mongo_client = MongoClient(f"mongodb+srv://JuneWay:{mongo_pwd}@ethanc.qgevd.mongodb.net/")
openai_client = OpenAI(api_key=openai_api_key)

db = mongo_client["JobDB"]
jobs_collection = db["jobs"]

# Testing if the openai api is working

test = openai_client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[{"role":"user","content":"Hello?"}]
)
print("OpenAI test reply:", test.choices[0].message.content)

def summarize_description(description):
    prompt = f"""
You’re a summarizer agent that helps job seekers.
Given a job description, do the following:
1. Write a 1–2 sentence summary.
2. List key technical skills in a comma separated words.
3. List degree/education requirements in a few words.

Respond in JSON with keys: summary, skills_desired, degree_qualifications.

Job Description:
\"\"\"{description}\"\"\"
"""
    resp = openai_client.chat.completions.create(
        model="o4-mini-2025-04-16",
        messages=[{"role": "user", "content": prompt}],
    )

    content = resp.choices[0].message.content.strip()
    return json.loads(content)

jobs = list(jobs_collection.find({"job_description": {"$exists": True}}))
for job in tqdm(jobs):
    desc = job["job_description"]
    try:
        result = summarize_description(desc)
        jobs_collection.update_one(
            {"_id": job["_id"]},
            {
                "$set": {
                    "summary":               result["summary"],
                    "skills_desired":        result["skills_desired"],
                    "degree_qualifications": result["degree_qualifications"],
                },
                "$unset": {"job_description": ""},
            }
        )
    except Exception as e:
        print(f"Failed on {job.get('job_title','<no title>')}: {e}")
