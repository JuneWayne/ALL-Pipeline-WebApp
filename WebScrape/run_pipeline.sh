#! /bin/bash
set -a
source .env
set +a

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