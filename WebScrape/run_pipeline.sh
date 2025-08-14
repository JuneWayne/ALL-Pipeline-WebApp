#! /bin/bash
set -a
source .env
set +a

set -euo pipefail

export $(grep -v '^#' /home/EthanCao/.env | xargs)

source /home/EthanCao/.virtualenvs/chatbot/bin/activate

echo "Running cleanup script..."
python3 clear_jobs.py

echo "Running scraper..."
python3 JobScraper.py

echo "Importing csv to MongoDB..."
python3 upload_to_mongo.py

echo "Running location encoder script..."
python3 latlong_US.py

echo "Running job summary generator script..."
python3 Job_info.py

echo "Running job summarizer script..."
python3 Job_Summarizer_Agent.py

echo "Running historical data upload script"
python3 upload_history.py

echo "Running chatbot ingestion script.."
python3 Chatbot_Ingestion.py

echo "Running elevenlabs RAG ingestion script"
python3 ElevenLabs_RAG_Indexing.py