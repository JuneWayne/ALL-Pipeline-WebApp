import os
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import warnings
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from langchain.docstore.document import Document
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
import json

warnings.filterwarnings("ignore")
load_dotenv('.env')

API_URL = "https://jobdata-cih4.onrender.com/api/jobs"
INDEX_NAME = "csv-jobdata-index"
PINECONE_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = os.getenv("PINECONE_ENV")
EMBED_MODEL = "text-embedding-ada-002"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/115.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
}

if not PINECONE_KEY or not PINECONE_ENV:
    print("Missing Pinecone credentials in .env")
    exit(1)

pc = Pinecone(api_key=PINECONE_KEY)

if not pc.has_index(INDEX_NAME):
    pc.create_index(
        name=INDEX_NAME,
        dimension=1536,
        metric="cosine",
        spec=ServerlessSpec(
            cloud="aws",
            region=PINECONE_ENV
        )
    )

index = pc.Index(INDEX_NAME)

stats = index.describe_index_stats()

if not stats.namespaces:
    print("Index is empty; nothing to delete.")
else:
    for ns, meta in stats.namespaces.items():
        vc = meta.get("vector_count", 0)
        if vc > 0:
            print(f"Clearing {vc} vectors from namespace {ns!r}…")
            index.delete(delete_all=True, namespace=ns)
        else:
            print(f"Namespace {ns!r} is already empty; skipping.")
    print("Done.")



session = requests.Session()
retries = Retry(
    total=5,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"],
)

adapter = HTTPAdapter(max_retries=retries)
session.mount("https://", adapter)
session.mount("http://", adapter)

def fetch_jobs_from_api(url: str) -> list[dict]:
    try:
        # (5s connect timeout, 60s read timeout)
        resp = session.get(url, headers=HEADERS, timeout=(5, 60))
        resp.raise_for_status()
    except requests.exceptions.ReadTimeout:
        print("Read timeout; consider increasing the read timeout or check API health.")
        return []
    except requests.exceptions.RequestException as e:
        print("Failed to fetch jobs:", e)
        return []

    print("HTTP status:", resp.status_code)
    data = resp.json()
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "jobs" in data:
        return data["jobs"]

    print("Unexpected JSON shape; returning empty list")
    return []


def docs_from_jobs(jobs: list[dict]) -> list[Document]:
    docs = []
    for job in jobs:
        json_blob = json.dumps(job, ensure_ascii=False)
        docs.append(Document(
            page_content=json_blob,
            metadata={"id": str(job.get("id", job.get("url", "")))}
        ))
    return docs

def update_vector_store():
    print(f"Fetching jobs from {API_URL} …")
    jobs = fetch_jobs_from_api(API_URL)
    print(f"Got {len(jobs)} jobs")

    # text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    # docs = docs_from_jobs(jobs)
    # chunks = text_splitter.split_documents(docs)
    # print(f"Split into {len(chunks)} chunks")

    docs = docs_from_jobs(jobs)
    store = PineconeVectorStore.from_documents(
        documents=docs,
        index_name=INDEX_NAME,
        embedding=OpenAIEmbeddings(model=EMBED_MODEL),
    )

    print("Upsert complete.")

if __name__ == "__main__":
    update_vector_store()
