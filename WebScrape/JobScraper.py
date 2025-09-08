# KNOWN ISSUES OF THIS SCRIPT:
# The script currently only produces job title, post date, number of application, and job description

# ADVANTAGES OF THIS SCRIPT:
# has the ability to scrape LinkedIn using its own api without the risk of being blocked or banned

import time
import requests
from bs4 import BeautifulSoup, Comment
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GOOGLE_PSE_API_KEY")
CX = os.getenv("GOOGLE_PSE_CX")

# Customize the scrape with job title and job location
title = "Data Intern"
location = "United States"
job_list = []
start_time = time.time()  # Record the start time
runtime_limit = 120  # Force scraping to run for at least 60 seconds

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/115.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
}

def extract_application_link(job_soup):
    code = job_soup.find('code', id='applyUrl')
    if not code:
        return None
    # get the first HTML comment inside the <code> node
    comment = code.find(string=lambda s: isinstance(s, Comment))
    if not comment:
        return None
    return comment.strip().strip('"')

# Customize the starting point of the webpage, eg. start scraping at 0 until page 500 with an increment of 25 pages each time
# technically, the larger the range, the more output it will produce, however the results can vary from time to time
while time.time() - start_time < runtime_limit:
  for start in range(0, 1500, 25):
    list_url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={title}&location={location}&start={start}"
    response = requests.get(list_url, headers=HEADERS)
    #if response.status_code != 200:
        #print(f"Failed to retrieve jobs for start={start}, status={response.status_code}")
        #continue

    list_data = response.text
    list_soup = BeautifulSoup(list_data, "html.parser")
    page_jobs = list_soup.find_all("li")

    id_list = []
    for job in page_jobs:
        base_card_div = job.find("div", {"class": "base-card"})
        if base_card_div:
            job_id = base_card_div.get("data-entity-urn").split(":")[3]
            id_list.append(job_id)

    for job_id in id_list:
        job_url = f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"
        job_response = requests.get(job_url)
        #if job_response.status_code != 200:
            #print(f"Failed to retrieve job details for job_id={job_id}, status={job_response.status_code}")
            #continue

        job_soup = BeautifulSoup(job_response.text, "html.parser")
        job_post = {}

        try:
            job_post["job_title"] = job_soup.find("h2", {"class": "top-card-layout__title"}).text.strip()
        except:
            job_post["job_title"] = None

        try:
            job_post["company_name"] = job_soup.find("a", {"class": "topcard__org-name-link"}).text.strip()
        except:
            job_post["company_name"] = None

        try:
          job_post["location"] = job_soup.find("span", {"class": "topcard__flavor topcard__flavor--bullet"}).text.strip()
        except:
          job_post["location"] = None

        try:
            job_post["time_posted"] = job_soup.find("span", {"class": "posted-time-ago__text"}).text.strip()
        except:
            job_post["time_posted"] = None

        try:
            job_post["num_applicants"] = job_soup.find("span", {"class": "num-applicants__caption"}).text.strip()
        except:
            job_post["num_applicants"] = None
        # try:
        #     job_post["Seniority Level"] = job_soup.find("span", {"class": "description__job-criteria-text description__job-criteria-text--criteria"}).text.strip()
        # except:
        #     job_post["Seniority Level"] = None

        # try:
        #     job_post["Employment Type"] = job_soup.find("span", {"class": "description__job-criteria-text description__job-criteria-text--criteria"}).text.strip()
        # except:
        #     job_post["Employment Type"] = None

        # try:
        #     job_post["Job Function"] = job_soup.find("span", {"class": "description__job-criteria-text description__job-criteria-text--criteria"}).text.strip()
        # except:
        #     job_post["Job Function"] = None
        # Dynamically extract criteria like Seniority Level, Employment Type, etc.
        criteria_items = job_soup.find_all("li", class_="description__job-criteria-item")

        for item in criteria_items:
            try:
                header = item.find("h3", class_="description__job-criteria-subheader").text.strip()
                value = item.find("span", class_="description__job-criteria-text description__job-criteria-text--criteria").text.strip()

                if "Seniority" in header:
                    job_post["Seniority Level"] = value
                elif "Employment" in header:
                    job_post["Employment Type"] = value
                elif "Job function" in header:
                    job_post["Job Function"] = value
                elif "Industries" in header:
                    job_post["Industries"] = value
            except:
                continue


        try:
            job_post["job_description"] = job_soup.find("div", {"class": "decorated-job-posting__details"}).text.strip()
        except:
            job_post["job_description"] = None
        try:
            job_post["application_link"] = extract_application_link(job_soup)
        except:
            job_post["applicaiton_link"] = None

        job_post["job_link"] = f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"

        # USING GOOGLE PSE (CUSTOMIZED SEARCH ENGINE) TO SCRAPE RECRUITER INFORMATION
        company_name = job_soup.find("a", {"class": "topcard__org-name-link"}).text.strip()
        search_query = f"{company_name} campus recruiter"
        url = 'https://www.googleapis.com/customsearch/v1'

        params = {
            'q': search_query,
            'key': API_KEY,
            'cx': CX,
            'num': 10,
            'start': 1,
            'gl': 'US',
        }
        response = requests.get(url, params=params)
        data = response.json()

        for item in data['items']:
            recruiter_name = item['title']
            recruiter_link = item['link']
            # print(item['title'])
            # print(item['link'])
            # print('\n')
            job_post["potential_recruiters"] = recruiter_name + ": " + recruiter_link
        job_list.append(job_post)

df = pd.DataFrame(job_list)
df = df.dropna(subset=['job_title']) if df['job_title'].isnull().any() else df
df.to_csv('Data_Science_Internship_Full.csv', index = False)
