# Active Learning Lab DSCareers Website Pipeline 
<table>
<tr>
<td>
  A dynamic web application that showcases real-time job postings and interactive analytical visualizations. It features an automated data pipeline with scheduled scraping tasks, seamless ingestion into MongoDB, integration with FastAPI deployed via Render, and real-time data rendering through auto-fetched API endpoints via JavaScript.
</td>
</tr>
</table>


## Demo:
Here is a working live demo : https://dscareers-ethancao.pythonanywhere.com/US_map
<img src="./misc/Demo-2.png" alt="demo image">

## Built with: 
- `Front End`: HTML, CSS, JavaScript, Streamlit
- `Back End`: Flask, Shell, FastAPI, MongoDB, CORSMiddleware
- `Web-scrape & Data Processing`: BeautifulSoup4, Requests, Pandas, Numpy
- `API`: Job Data guest API, openstreetmap.org API, Render Cloud Services API (for shipping)
- `Chatbot (Summarizer)`: OpenAI o4-mini, Langchain, Pinecone, StreamLit
- `Chatbot (Copilot Agent)`: OpenAI GPT-4o, Langchain, Pinecone, Streamlit, ElevenLabs

## Pipeline Architecture:
<img src="./misc/Data_Pipeline(1).png" alt="data pipeline">

## Update Log:
**03/05**
- Optimize webscraping scripts to fully utilize the given guest-api
- Extract as much valuable components from the api as possible
- automate the data pre-processing stage, and export as a csv file
  
**03/19**
- Establish the basic architecture of the website landing page via HTML + CSS
- Write sample article title pages to simulate that of a real website
  
**04/02**
- Establish a basic HTML + CSS structure of the visualization pages, create new endpoints for users to access
- Design the interactive components (via JavaScript) on the visual map that connects to the csv data tables scraped from webscraper
- Create a script that auto-encodes location names from the dataset into geo LAT LONG coordinates
  
**04/16**
- Automate the web-scrape task and connect it with MongoDB via Shell 
- initialize the pipeline and create a fastapi end point up running in the cloud (so that the website can always access it)
- consider whether a paid tier is required for Render's cloud api services

**05/16**
- Established scheduled tasks via Pythonanywhere to collect internship updates on a daily basis at 6AM eastern
- Created a Job Description Summarizer Agent that parses key information such as degree requirement, skills desired, and job duties
- Created an Internship Copilot Agent via Streamlit that finds relevant internship recommendations based on user query from Pinecone's Vector Store
- Embedded Streamlit application to Front-end website
- Connected Front-end displays with Render API

**06/30**
- Fixed the pipeline breakage from OpenAI Errors and migrated deprecated Pinecone packages to newer updates
- Connected the Pinecone Vector Store with the scheduled data pipeline, automated the embedding process to ensure that the chatbot is update-to-date with the newest internship information

**07/02**
- Automated the RAG ingestion process for Elevenlab's conversational AI Agent via script

**07/04**
- Added more UI features such as collapsable chatbox, separated conversational AI widget location, loading screen spinner, and the zoom-in/zoom-out aggregation of job markers on the map
- Fine-tuned conversational AI's prompt, voice parameters, quality of output
- Optimized the web-scraping script to avoid being rate-limited 

## To Dos 🚨
- Fix bugs of location markers showing 'zero' jobs ✅
- Fix bugs of location markers overlapping each other on the same long/latitude position ✅
- Fix Chatbot's connection to Pinecone (JSON format versus Document format retrievals) ✅
- Fix Conversational AI's 'Permission Denied' issue ✅
- Add MSDS Alumni profile from Wahoo Connect

## Future Steps 🔮
- Create an analytical dashboard of visualizations via D3 or Python that is connected to the cloud api
- Make the chatbot interface collapsable ✅
- Improve UI for better user experience overall (smoother transitions, aggregating markers when zoomed out, etc) ✅
- Scrape Alumni profile information (MSDS Alumni, UVA Alums in general) and link it to the relevant job postings
- Scrape HR contact + application link information for each job postings

### How to test pipeline:
1. source ~/.virtualenvs/chatbot/bin/activate
2. chmod 755 run_pipeline.sh
3. ./run_pipeline.sh


