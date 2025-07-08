import os
import time
import requests
from dotenv import load_dotenv
from elevenlabs import ElevenLabs

load_dotenv()

API_KEY = os.getenv("ELEVENLABS_API_KEY")
ORIG_DOC_ID = os.getenv("DOCUMENT_ID")
AGENT_ID = os.getenv("AGENT_ID")
API_URL = "https://jobdata-cih4.onrender.com/api/jobs"
EMBEDDING_MODEL = "e5_mistral_7b_instruct"
POLL_INTERVAL = 1

if not all([API_KEY, ORIG_DOC_ID, AGENT_ID, API_URL]):
    raise RuntimeError("Missing one of ELEVENLABS_API_KEY, DOCUMENT_ID, AGENT_ID or JOB_API_URL in .env")

def main():
    client = ElevenLabs(api_key=API_KEY)

    resp = requests.get(API_URL)
    resp.raise_for_status()
    print(f"Fetched API data ({len(resp.text)} bytes)")

    try:
        client.conversational_ai.knowledge_base.documents.delete(
            documentation_id=ORIG_DOC_ID
        )
        print(f"Deleted old document {ORIG_DOC_ID}")
    except Exception as e:
        print(f"Warning: could not delete existing doc: {e}")

    new_doc = client.conversational_ai.knowledge_base.documents.create_from_url(
        url=API_URL,
        name="Job-Data API Doc"
    )
    KB_DOC_ID = new_doc.id
    print(f"Created new document {KB_DOC_ID}")

    doc_info = client.conversational_ai.knowledge_base.documents.get(
        documentation_id=KB_DOC_ID
    )
    doc_name = doc_info.name
    doc_type = doc_info.type

    idx = client.conversational_ai.knowledge_base.document.compute_rag_index(
        documentation_id=KB_DOC_ID,
        model=EMBEDDING_MODEL
    )
    while idx.status.lower() not in ("succeeded", "failed"):
        print(f"[RAG] status: {idx.status}, retrying in {POLL_INTERVAL}s…")
        time.sleep(POLL_INTERVAL)
        idx = client.conversational_ai.knowledge_base.document.compute_rag_index(
            documentation_id=KB_DOC_ID,
            model=EMBEDDING_MODEL
        )
    if idx.status.lower() == "failed":
        raise RuntimeError("RAG indexing failed")
    print(f"RAG indexing completed with status: {idx.status}")

    agent_resp = client.conversational_ai.agents.get(agent_id=AGENT_ID)
    cfg = agent_resp.conversation_config    # frozen Pydantic model

    prompt_model   = cfg.agent.prompt
    updated_prompt = prompt_model.model_copy(update={
        "rag": {
            "enabled": True,
            "embedding_model": EMBEDDING_MODEL,
            "max_documents_length": 10_000
        },
        "knowledge_base": [{
            "id": KB_DOC_ID,
            "name": doc_name,
            "type": doc_type,
            "usage_mode": "auto"
        }]
    })

    agent_model   = cfg.agent
    updated_agent = agent_model.model_copy(update={"prompt": updated_prompt})

    new_cfg = cfg.model_copy(update={"agent": updated_agent})

    client.conversational_ai.agents.update(
        agent_id=AGENT_ID,
        conversation_config=new_cfg
    )

    print("Sync + RAG update complete.")

if __name__ == "__main__":
    main()
