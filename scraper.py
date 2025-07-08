import requests
from pymongo import MongoClient
import time
from itertools import cycle
import os 

SERPER_API_KEYS = os.getenv("SERPER_API_KEYS", "").split(",")
serper_key_cycle = cycle(SERPER_API_KEYS) 
mongo_uri = os.getenv("MONGODB_URI")


def get_jobs_for_query_country(query, country_domain, country_code, country, continent, pages=4, new=True):
    all_jobs = []
    for page in range(pages):
        freshness = "after:2025-01-01" if new else ""
        search_query = f"site:{country_domain}/jobs {query} {freshness}".strip()

        payload = {
            "q": search_query,
            "num": 10,
            "start": page * 10
        }

        max_attempts = len(SERPER_API_KEYS)
        attempt = 0

        while attempt < max_attempts:
            current_key = next(serper_key_cycle)
            headers = {
                "X-API-KEY": current_key,
                "Content-Type": "application/json"
            }

            try:
                response = requests.post(
                    "https://google.serper.dev/search",
                    json=payload,
                    headers=headers,
                    timeout=15
                )

                if response.status_code == 200:
                    data = response.json()
                    organic = data.get("organic", [])
                    break
                else:
                    print(f"❌ Key #{attempt+1} failed (Status: {response.status_code})")
                    attempt += 1
                    time.sleep(1)

            except Exception as e:
                print(f"⚠️ Key #{attempt+1} error: {e}")
                attempt += 1
                time.sleep(1)

        else:
            print(f"❌ All API keys failed for '{query}' in {country_code.upper()}")
            return []

        if not organic:
            print(f"❌ No results on page {page + 1} for '{query}' in {country_code}")
            continue

        print(f"✅ {country_code.upper()} Page {page + 1}: Found {len(organic)} results for '{query}'")

        for result in organic:
            link = result.get("link", "").strip()
            title = result.get("title", "").strip()

            # ✅ Only accept actual job detail pages
            if any(p in link for p in ["/viewjob?jk=", "/rc/clk?jk="]) and country_domain in link:
                all_jobs.append({
                    "title": title,
                    "job_url": link,
                    "country": country,
                    "is_new": new,
                    "country_code": country_code.upper(),
                    "continent": continent,
                })
                print(f"→ {title} | {link}")

        time.sleep(1)

    return all_jobs


def save_to_mongodb(data, db_name="Indeed_jobs_urls", collection_name="Indeed_database", uri=mongo_uri):
    try:
        # Connect to MongoDB
        client = MongoClient(uri)
        db = client[db_name]
        collection = db[collection_name]

        # Ensure data is a list
        if isinstance(data, dict):
            data = [data]
        elif not isinstance(data, list):
            print("Data must be a dictionary or list of dictionaries.")
            return
    
        inserted_count = 0
        for doc in data:
            # Check if the document already exists
            if not collection.find_one({"job_url": doc.get("job_url")}):
                collection.insert_one(doc)
                inserted_count += 1
        
        print(f"Inserted {inserted_count} new documents.")

    except Exception as e:
        print(f"Error saving to MongoDB: {e}")


if __name__ == "__main__":
    
    
    #keywords 0 = ["remote " + skill for skill in skills]
    keywords_0 = [
        "Jobs for Moroccans", "Jobs for people from Morocco", "We are hiring from Morocco", "Remote jobs Morocco", "Moroccan remote jobs",
        "Hiring Moroccan freelancers", "Freelance jobs Morocco", "Open to Moroccan candidates", "Looking for Moroccan workers","Jobs for North Africa", "Remote jobs Maghreb", "Maghrib remote work", "Hiring from المغرب", "Maroc jobs remote",
        "Marocain freelance", "We hire from Maghreb", "Accepting applicants from Morocco", "Open to North African applicants",
        "Remote jobs for المغرب", "International jobs for Moroccans", "EMEA" , 
    ]
    
    #keywords 1 = ["remote " + Junior Developer (Web, App, etc.)]
    keywords_1 = [
        "Work from home", "Remote part-time", "Online jobs", "Remote tasks", "Freelance work", "Online data entry",
        "Remote typing jobs", "Remote virtual assistant", "Remote transcription", "Remote microtasks", 
        "Part-time remote assistant", "Online research jobs", "Remote survey jobs",
        "Freelance content writer", "Remote customer support", "Remote moderator", 
        "Remote administrative assistant", "Remote chat support", "Remote captioning",
    ]
    
    #keywords 2 = ["remote " + Junior Developer (Web, App, etc.)]
    keywords_2= [
        "Junior web developer", "Entry level web developer", "Remote junior developer", "Junior frontend developer", "Junior backend developer","React developer intern", "Remote Node.js developer",
        "Junior full stack developer", "Remote Django developer", "Junior software engineer", "Remote Flutter developer", "Remote Python developer", "Remote Laravel developer", "Remote JavaScript developer",
        "Remote WordPress developer", "Junior mobile app developer", "Remote developer internship", "Junior dev remote", "Remote backend intern", "Entry level software developer"
        ]
    
    #keywords 3 = ["remote " + Junior / Entry-Level Data Analyst]
    keywords_3 = [
        "Junior data analyst", "Entry level data analyst", "Remote data analyst", "Data analyst internship", "Junior business analyst",
        "Data entry analyst remote", "Remote reporting analyst", "Data analyst trainee", "Remote BI analyst", "SQL analyst remote", 
        "Remote Excel analyst", "Entry data scientist", "Remote statistics analyst", "Junior data visualization", "Remote Tableau analyst",
        "Remote Power BI analyst", "Remote ETL intern", "Data operations remote", "Remote analytics intern"
     ]
    
    #keywords 4 = ["remote " + Other Remote Jobs You Can Likely Do]
    keywords_4 = [ 
        "Remote data entry",  "Remote research assistant",  "Remote QA tester",  "Remote software tester intern",  "Remote technical support",
        "Remote web researcher", "Remote customer service", "Remote assistant", "Remote content moderator", "Remote social media assistant", "Remote online tutor",
        "Remote transcriptionist", "Remote content creator", "Remote email handler", "Remote operations assistant", "Remote product tester",
        "Remote CRM support", "Remote intern", "Remote virtual assistant"
    ]
    
    keywords_5 = [
        "Remote internship", "Remote jobs worldwide", "Work from anywhere", "Remote job anywhere", "Remote freelance job",
        "Remote junior job", "Global remote job", "Remote contract job", "Remote international job", "Worldwide data entry",
        "Anywhere job internship", "Remote developer worldwide", "Remote analyst anywhere", "Online job international", 
        "Remote tech support global", "Remote admin job international"
    ]
    
    keywords_6 = [
        "Visa sponsorship", "Jobs with visa sponsorship", "H1B sponsorship", "Skilled worker visa", "Sponsorship jobs abroad", "Sponsorship jobs Europe",
        "Junior jobs with sponsorship", "Remote jobs with visa sponsorship", "Work permit jobs", "Tier 2 sponsorship", "Tech jobs with visa support",
        "Relocation and visa support","Internship with sponsorship","International relocation jobs","Jobs hiring foreign workers","Jobs open to international candidates",
        "Sponsorship jobs remote", "Remote jobs for foreigners", "Hiring international talent", "Global talent visa jobs"
        ]
    
    keywords_7= [
        "remote data analyst", "remote python developer", "remote junior data",
        "remote associate developer", "remote data annotator", "remote data entry",
        "remote data collection", "remote web scraping", "remote data cleaning",
        "remote arabic data", "remote morocco data", "remote AI data trainer",
        "remote prompt engineer", "remote sports data scientist", "remote web3 data analyst",
        "remote voice data curator", "remote low-code developer", "content moderation"
    ]
    
    keywords = keywords_1
   
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



    

    for country_code, data in country_data.items():
        all_results = []
        domain = data["domain"]
        keywords = data["keywords"]
        country = data["country"]
        continent = data["continent"]

        for keyword in keywords:
            print(f"\n🔎 Searching '{keyword}' in {country_code.upper()}")
            jobs = get_jobs_for_query_country(
                keyword, domain, country_code, country ,continent , pages=4, new=True
            )
            all_results.extend(jobs)
        
        print(f"\n🎯 Total jobs scraped in : {country_code} is {len(all_results)}")
        save_to_mongodb(all_results)

