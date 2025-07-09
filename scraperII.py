from pymongo import MongoClient
import requests
from bs4 import BeautifulSoup
import time, os, random

CRAWLBASE_TOKEN = os.getenv("CRAWLBASE_TOKEN")
mongo_uri = os.getenv("MONGODB_URI")


def get_indeed_jobs(query, country_domain, country, pages):
    query = query.replace(" ", "+")
    results = []

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        )
    }

    for page in range(pages):
        url = f"https://{country_domain}/jobs?q={query}&start={page * 10}"
        print(f"\n🔎 Fetching: {url}")

        for attempt in range(5):
            try:
                crawlbase_url = f"https://api.crawlbase.com/?token={CRAWLBASE_TOKEN}&url={url}&autoparse=true"
                response = requests.get(crawlbase_url, headers=headers, timeout=15)

                if response.status_code != 200:
                    print(f"❌ Status {response.status_code} on attempt {attempt+1}")
                    time.sleep(random.uniform(2, 4))
                    continue

                soup = BeautifulSoup(response.text, "html.parser")
                jobs_container = soup.find("div", id="mosaic-provider-jobcards")
                job_cards = jobs_container.find_all("a", class_="tapItem") if jobs_container else []

                print(f"✅ Found {len(job_cards)} job cards")

                for card in job_cards:
                    try:
                        title_el = card.find("h2")
                        title = title_el.get_text(strip=True) if title_el else None

                        company_el = card.find("span", attrs={"data-testid": "company-name"})
                        location_el = card.find("div", attrs={"data-testid": "text-location"})
                        easy_apply = bool(card.find("span", {"data-testid": "indeedApply"}))

                        href = card.get("href")
                        job_url = f"https://{country_domain}{href}" if href and href.startswith("/rc/") or href.startswith("/pagead/") or href.startswith("/company/") or href.startswith("/viewjob") else None

                        if job_url and title:
                            results.append({
                                "title": title,
                                "company": company_el.get_text(strip=True) if company_el else None,
                                "location": location_el.get_text(strip=True) if location_el else None,
                                "country": country.upper(),
                                "job_url": job_url,
                                "easy_apply": easy_apply,
                                "is_new": True
                            })
                    except Exception as e:
                        print(f"⚠️ Job parse error: {e}")
                break  # Exit retry loop on success

            except Exception as e:
                print(f"⚠️ Request error: {e}")
                time.sleep(random.uniform(2, 4))

    return results


def save_to_mongodb(
        data, 
        db_name="Indeed_jobs_urls",
        collection_name="Indeed_database",
         uri=mongo_uri):
    try:
        client = MongoClient(uri)
        db = client[db_name]
        collection = db[collection_name]

        inserted_count = 0
        for doc in data:
            if not collection.find_one({"job_url": doc.get("job_url")}):
                collection.insert_one(doc)
                inserted_count += 1
        print(f"Inserted {inserted_count} new documents.")

    except Exception as e:
        print(f"❌ MongoDB Error: {e}")






#keywords 0 = ["remote " + skill for skill in skills]
keywords_00 = [
    "Jobs for Moroccans", "Jobs for people from Morocco", "We are hiring from Morocco", "Remote jobs Morocco", "Moroccan remote jobs",
    "Hiring Moroccan freelancers", "Freelance jobs Morocco", "Open to Moroccan candidates", "Looking for Moroccan workers","Jobs for North Africa", "Remote jobs Maghreb", "Maghrib remote work", "Hiring from المغرب", "Maroc jobs remote",
    "Marocain freelance", "We hire from Maghreb", "Accepting applicants from Morocco", "Open to North African applicants",
    "Remote jobs for المغرب", "International jobs for Moroccans", "EMEA" , 
]
keywords_01= [
    "remote data analyst", "remote python developer", "remote junior data",
    "remote associate developer", "remote data annotator", "remote data entry",
    "remote data collection", "remote web scraping", "remote data cleaning",
    "remote arabic data", "remote morocco data", "remote AI data trainer",
    "remote prompt engineer", "remote sports data scientist", "remote web3 data analyst",
    "remote voice data curator", "remote low-code developer", "content moderation"
]

#keywords 1 = ["remote " + Junior Developer (Web, App, etc.)]
keywords_1 = [
    "Work from home",
    "Remote part-time",
    "Online jobs",
    "Remote tasks",
    "Freelance work",
    "Online data entry",
    "Remote typing jobs",
    "Remote virtual assistant",
    "Remote transcription",
    "Remote microtasks",
    "Part-time remote assistant",
    "Online research jobs",
    "Remote survey jobs",
    "Freelance content writer",
    "Remote customer support",
    "Remote moderator",
    "Remote administrative assistant",
    "Remote chat support",
    "Remote captioning",
]

#keywords 2 = ["remote " + Junior Developer (Web, App, etc.)]
keywords_2= [
    "Junior web developer",
    "Entry level web developer",
    "Remote junior developer",
    "Junior frontend developer",
    "Junior backend developer",
    "React developer intern",
    "Remote Node.js developer",
    "Junior full stack developer",
    "Remote Django developer",
    "Junior software engineer",
    "Remote Flutter developer",
    "Remote Python developer",
    "Remote Laravel developer",
    "Remote JavaScript developer",
    "Remote WordPress developer",
    "Junior mobile app developer",
    "Remote developer internship",
    "Junior dev remote",
    "Remote backend intern",
    "Entry level software developer"
]

#keywords 3 = ["remote " + Junior / Entry-Level Data Analyst]
keywords_3 = [
    "Junior data analyst",
    "Entry level data analyst",
    "Remote data analyst",
    "Data analyst internship",
    "Junior business analyst",
    "Data entry analyst remote",
    "Remote reporting analyst",
    "Data analyst trainee",
    "Remote BI analyst",
    "SQL analyst remote",
    "Remote Excel analyst",
    "Entry data scientist",
    "Remote statistics analyst",
    "Junior data visualization",
    "Remote Tableau analyst",
    "Remote Power BI analyst",
    "Remote ETL intern",
    "Data operations remote",
    "Remote analytics intern"
]

#keywords 4 = ["remote " + Other Remote Jobs You Can Likely Do]
keywords_4 = [
    "Remote data entry",
    "Remote research assistant",
    "Remote QA tester",
    "Remote software tester intern",
    "Remote technical support",
    "Remote web researcher",
    "Remote customer service",
    "Remote assistant",
    "Remote content moderator",
    "Remote social media assistant",
    "Remote online tutor",
    "Remote transcriptionist",
    "Remote content creator",
    "Remote email handler",
    "Remote operations assistant",
    "Remote product tester",
    "Remote CRM support",
    "Remote intern",
    "Remote virtual assistant"
]


#keywords 5 = ["remote " + Remote Jobs Anywhere in the World]
keywords_5 = [
    "Remote internship",
    "Remote jobs worldwide",
    "Work from anywhere",
    "Remote job anywhere",
    "Remote freelance job",
    "Remote junior job",
    "Global remote job",
    "Remote contract job",
    "Remote international job",
    "Worldwide data entry",
    "Anywhere job internship",
    "Remote developer worldwide",
    "Remote analyst anywhere",
    "Online job international",
    "Remote tech support global",
    "Remote admin job international"
]

#keywords 6 = ["remote " + Jobs That Provide Sponsorship]
keywords_6 = [
    "Visa sponsorship",
    "Jobs with visa sponsorship",
    "H1B sponsorship",
    "Skilled worker visa",
    "Sponsorship jobs abroad",
    "Sponsorship jobs Europe",
    "Junior jobs with sponsorship",
    "Remote jobs with visa sponsorship",
    "Work permit jobs",
    "Tier 2 sponsorship",
    "Tech jobs with visa support",
    "Relocation and visa support",
    "Internship with sponsorship",
    "International relocation jobs",
    "Jobs hiring foreign workers",
    "Jobs open to international candidates",
    "Sponsorship jobs remote",
    "Remote jobs for foreigners",
    "Hiring international talent",
    "Global talent visa jobs"
]



keywords = keywords_00
max_pages = 5


country_data = {
    "us": {"country": "United States", "domain": "indeed.com", "keywords": keywords, "continent": "North America"},
    "ca": {"country": "Canada", "domain": "ca.indeed.com", "keywords": keywords, "continent": "North America"},
    "fr": {"country": "France", "domain": "fr.indeed.com", "keywords": keywords, "continent": "Europe"},
    "es": {"country": "Spain", "domain": "es.indeed.com", "keywords": keywords, "continent": "Europe"},
    "it": {"country": "Italy", "domain": "it.indeed.com", "keywords": keywords, "continent": "Europe"},
    "ch": {"country": "Switzerland", "domain": "ch.indeed.com", "keywords": keywords, "continent": "Europe"},
    "be": {"country": "Belgium", "domain": "be.indeed.com", "keywords": keywords, "continent": "Europe"},
    "pt": {"country": "Portugal", "domain": "pt.indeed.com", "keywords": keywords, "continent": "Europe"},
    "se": {"country": "Sweden", "domain": "se.indeed.com", "keywords": keywords, "continent": "Europe"},
    "de": {"country": "Germany", "domain": "de.indeed.com", "keywords": keywords, "continent": "Europe"},
    "nl": {"country": "Netherlands", "domain": "nl.indeed.com", "keywords": keywords, "continent": "Europe"},
    "uk": {"country": "United Kingdom", "domain": "uk.indeed.com", "keywords": keywords, "continent": "Europe"},
    "ie": {"country": "Ireland", "domain": "ie.indeed.com", "keywords": keywords, "continent": "Europe"},
    "au": {"country": "Australia", "domain": "au.indeed.com", "keywords": keywords, "continent": "Oceania"},
    "ae": {"country": "United Arab Emirates", "domain": "ae.indeed.com", "keywords": keywords, "continent": "Asia"},
    "in": {"country": "India", "domain": "indeed.co.in", "keywords": keywords, "continent": "Asia"},
    "br": {"country": "Brazil", "domain": "indeed.com.br", "keywords": keywords, "continent": "South America"},
    "mx": {"country": "Mexico", "domain": "mx.indeed.com", "keywords": keywords, "continent": "North America"},
    "ar": {"country": "Argentina", "domain": "ar.indeed.com", "keywords": keywords, "continent": "South America"},
    "cl": {"country": "Chile", "domain": "cl.indeed.com", "keywords": keywords, "continent": "South America"},
    "co": {"country": "Colombia", "domain": "co.indeed.com", "keywords": keywords, "continent": "South America"},
    "cr": {"country": "Costa Rica", "domain": "cr.indeed.com", "keywords": keywords, "continent": "North America"},
    "cz": {"country": "Czech Republic", "domain": "cz.indeed.com", "keywords": keywords, "continent": "Europe"},
    "fi": {"country": "Finland", "domain": "fi.indeed.com", "keywords": keywords, "continent": "Europe"},
    "dk": {"country": "Denmark", "domain": "dk.indeed.com", "keywords": keywords, "continent": "Europe"},
    "no": {"country": "Norway", "domain": "no.indeed.com", "keywords": keywords, "continent": "Europe"},
    "pl": {"country": "Poland", "domain": "pl.indeed.com", "keywords": keywords, "continent": "Europe"},
    "ro": {"country": "Romania", "domain": "ro.indeed.com", "keywords": keywords, "continent": "Europe"},
    "hu": {"country": "Hungary", "domain": "hu.indeed.com", "keywords": keywords, "continent": "Europe"},
    "il": {"country": "Israel", "domain": "il.indeed.com", "keywords": keywords, "continent": "Asia"},
    "nz": {"country": "New Zealand", "domain": "nz.indeed.com", "keywords": keywords, "continent": "Oceania"},
    "sg": {"country": "Singapore", "domain": "sg.indeed.com", "keywords": keywords, "continent": "Asia"},
    "za": {"country": "South Africa", "domain": "za.indeed.com", "keywords": keywords, "continent": "Africa"},
    "jp": {"country": "Japan", "domain": "jp.indeed.com", "keywords": keywords, "continent": "Asia"},
    "kr": {"country": "South Korea", "domain": "kr.indeed.com", "keywords": keywords, "continent": "Asia"},
    "my": {"country": "Malaysia", "domain": "my.indeed.com", "keywords": keywords, "continent": "Asia"},
    "ph": {"country": "Philippines", "domain": "ph.indeed.com", "keywords": keywords, "continent": "Asia"},
    "ru": {"country": "Russia", "domain": "ru.indeed.com", "keywords": keywords, "continent": "Europe"},  # sometimes considered both Europe & Asia
    "th": {"country": "Thailand", "domain": "th.indeed.com", "keywords": keywords, "continent": "Asia"},
    "tr": {"country": "Turkey", "domain": "tr.indeed.com", "keywords": keywords, "continent": "Asia"},
    "vn": {"country": "Vietnam", "domain": "vn.indeed.com", "keywords": keywords, "continent": "Asia"},
}

# Scrape and analyze jobs
all_jobs = []
index = 0

for country_code, data in country_data.items():
        all_results = []
        domain = data["domain"]
        keywords_list = data["keywords"]
        country = data["country"]
        continent = data["continent"]

        jobs = get_indeed_jobs(keywords_list , domain, country , max_pages)
        all_jobs.extend(jobs)
        time.sleep(2)
        # remove duplicates
        unique_jobs_data = [dict(t) for t in {tuple(d.items()) for d in all_jobs}]
        # Save to mongodb
        if unique_jobs_data:
            save_to_mongodb(unique_jobs_data)
            print(f"Saved {len(unique_jobs_data)} jobs from {country}")
        else:
            print("No jobs found or saved.")