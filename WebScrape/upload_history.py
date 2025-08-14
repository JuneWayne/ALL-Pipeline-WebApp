import os, re
from datetime import datetime, timezone, timedelta
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()
mongo_pwd = os.getenv("MONGO_PWD")
mongo_uri = f"mongodb+srv://JuneWay:{mongo_pwd}@ethanc.qgevd.mongodb.net/JobDB"
client = MongoClient(mongo_uri)
db = client["JobDB"]

collection_daily = db["jobs"]           
collection_historical = db["jobs_history"]  

# anchor the time at 10:00 AM UTC
def get_scrape_anchor_utc(now_utc):
    anchor = now_utc.replace(hour=10, minute=0, second=0, microsecond=0)
    if now_utc < anchor:
        anchor -= timedelta(days=1)
    return anchor

def normalize_time_posted(raw, anchor_utc):  # <- added colon

    if not raw:
        return None, False
    s = str(raw).strip().lower()

    # Quick cases
    if s in {"now", "just now", "today"}:
        return anchor_utc, True
    if "yesterday" in s:
        return anchor_utc - timedelta(days=1), True

    # "30+ days ago"
    m = re.match(r"^\s*(\d+)\+\s*days?\s*ago\s*$", s)
    if m:
        n = int(m.group(1))
        return anchor_utc - timedelta(days=n), True
    
    patterns = [
        (r"^\s*(\d+)\s*(minutes?|mins?|m)\s*ago\s*$", "minutes"),
        (r"^\s*(\d+)\s*(hours?|hrs?|h)\s*ago\s*$",   "hours"),
        (r"^\s*(\d+)\s*(days?|d)\s*ago\s*$",         "days"),
        (r"^\s*(\d+)\s*(weeks?|wks?|w)\s*ago\s*$",   "weeks"),
        (r"^\s*(\d+)\s*(months?|mos?|mo)\s*ago\s*$", "months"),
        (r"^\s*(\d+)\s*(years?|yrs?|yr)\s*ago\s*$",  "years"),
    ]
    for pat, unit in patterns:
        m = re.match(pat, s)
        if m:
            n = int(m.group(1))
            if unit == "minutes":
                delta = timedelta(minutes=n)
            elif unit == "hours":
                delta = timedelta(hours=n)
            elif unit == "days":
                delta = timedelta(days=n)
            elif unit == "weeks":
                delta = timedelta(weeks=n)
            elif unit == "months":
                delta = timedelta(days=30 * n)  
            else:  # years
                delta = timedelta(days=365 * n) 
            return anchor_utc - delta, True

    # Fall back in case the scraped records has absolute dates
    for fmt in ("%Y-%m-%d", "%b %d, %Y", "%B %d, %Y", "%m/%d/%Y"):
        try:
            d = datetime.strptime(s, fmt).date()
            return datetime(d.year, d.month, d.day, tzinfo=timezone.utc), False
        except ValueError:
            pass

    return None, False   


BATCH_SIZE = 1000
now_utc = datetime.now(timezone.utc)
anchor_utc = get_scrape_anchor_utc(now_utc)

batch, inserted = [], 0
cursor = collection_daily.find({}, batch_size=BATCH_SIZE)

for doc in cursor:
    # copy the original id from the live database
    original_id = doc.pop("_id", None)
    doc["job_id"] = original_id  

    # compute absolute posted time
    raw = doc.get("time_posted")
    posted_at, x = normalize_time_posted(raw, anchor_utc)

    # create posted_at field
    doc["copied_at"] = now_utc.replace(tzinfo=None)
    if posted_at is not None:
        doc["posted_at"] = posted_at.replace(tzinfo=None)

    batch.append(doc)
    if len(batch) >= BATCH_SIZE:
        collection_historical.insert_many(batch, ordered=False)
        inserted += len(batch)
        batch.clear()

if batch:
    collection_historical.insert_many(batch, ordered=False)
    inserted += len(batch)

print(
    f"Copied {inserted} docs from 'jobs' to 'jobs_history' "
    f"(anchor={anchor_utc.isoformat()})."
)
