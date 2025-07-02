import os
import requests
import warnings
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from langchain.docstore.document import Document
from langchain.text_splitter import CharacterTextSplitter
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


def fetch_jobs_from_api(url: str) -> list[dict]:
    resp = requests.get(url, timeout=30, headers={"Accept": "application/json"})
    resp.raise_for_status()

    print("HTTP status:", resp.status_code)
    print("Raw body (first 500 chars):\n", resp.text[:500])

    data = resp.json()
    print("Parsed JSON:", type(data), data if isinstance(data, (list, dict)) else repr(data))

    if isinstance(data, list):
        return data

    if isinstance(data, dict) and "jobs" in data:
        return data["jobs"]

    print("⚠️  Unexpected JSON shape; returning empty list")
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
