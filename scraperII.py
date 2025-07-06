from pymongo import MongoClient
import requests
from bs4 import BeautifulSoup
import time , os
import random
import time

CRAWLBASE_TOKEN = os.getenv("CRAWLBASE_TOKEN")
mongo_uri = os.getenv("MONGODB_URI")


proxy_list = [
    "113.160.132.195:8080",
    "51.81.245.3:17981"
]
def get_indeed_jobs(query, country_domain, country, pages, CRAWLBASE_TOKEN, proxy_list):
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

        success = False
        retries = 0

        while not success and retries < 5:
            proxy = random.choice(proxy_list)
            proxies = {
                "http": f"http://{proxy}",
                "https": f"http://{proxy}"
            }

            try:
                response = requests.get(
                    f"https://api.crawlbase.com/?token={CRAWLBASE_TOKEN}&url={url}",
                    headers=headers,
                    proxies=proxies,
                    timeout=15
                )

                if response.status_code == 200:
                    success = True
                    soup = BeautifulSoup(response.text, "html.parser")
                    jobs_container = soup.find("div", id="mosaic-provider-jobcards")
                    job_cards = jobs_container.find_all("li") if jobs_container else []

                    print(f"✅ Found {len(job_cards)} job cards")

                    for card in job_cards:
                        try:
                            title_tag = card.find("h2")
                            link_tag = title_tag.find("a") if title_tag else None
                            id_tag = link_tag.get("id").replace("job_", "") if link_tag else None

                            company_tag = card.find("span", attrs={"data-testid": "company-name"})
                            location_tag = card.find("div", attrs={"data-testid": "text-location"})
                            easy_apply = bool(card.find("span", {"data-testid": "indeedApply"}))

                            title = title_tag.text.strip() if title_tag else None
                            company = company_tag.text.strip() if company_tag else None
                            location = location_tag.text.strip() if location_tag else None
                            job_url = f"https://{country_domain}/viewjob?jk={id_tag}" if id_tag else None

                            if title and job_url:
                                results.append({
                                    "title": title,
                                    "company": company,
                                    "location": location,
                                    "country": country.upper(),
                                    "job_url": job_url,
                                    "easy_apply": easy_apply
                                })
                        except Exception as e:
                            print(f"⚠️ Parse error: {e}")
                    break
                else:
                    print(f"❌ Status code {response.status_code} from Crawlbase.")
                    retries += 1
                    time.sleep(random.uniform(2, 5))
            except Exception as e:
                print(f"⚠️ Proxy failed ({proxy}): {e}")
                retries += 1
                time.sleep(random.uniform(2, 5))

    return results


def save_to_mongodb(data, db_name="Indeed_jobs_urls", collection_name="Indeed_urls", uri=mongo_uri):
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
                doc["is_new"] = True
                collection.insert_one(doc)
                inserted_count += 1
                print(f"Inserted {inserted_count} new documents.")

    except Exception as e:
        print(f"Error saving to MongoDB: {e}")



# Customize with your resume or preferences
countries= [
    "Netherlands", 
    #"Ireland", "Portugal", "Sweden", "Czech Republic", "Poland", "Italy", "Belgium", "Spain", "Switzerland", "Gibraltar"
]

#keywords 0 = ["remote " + skill for skill in skills]
keywords = [
    "Jobs for Moroccans", "Jobs for people from Morocco", "We are hiring from Morocco", "Remote jobs Morocco", "Moroccan remote jobs",
    "Hiring Moroccan freelancers", "Freelance jobs Morocco", "Open to Moroccan candidates", "Looking for Moroccan workers","Jobs for North Africa", "Remote jobs Maghreb", "Maghrib remote work", "Hiring from المغرب", "Maroc jobs remote",
    "Marocain freelance", "We hire from Maghreb", "Accepting applicants from Morocco", "Open to North African applicants",
    "Remote jobs for المغرب", "International jobs for Moroccans", "EMEA"
]





max_pages = 5

# Indeed country-specific domains
country_domains = {
  "USA": "www.indeed.com",
  "Canada": "ca.indeed.com",
  "Germany": "de.indeed.com",
  "Singapore": "sg.indeed.com",
  "New Zealand": "nz.indeed.com",
  "Austria": "at.indeed.com",
  "Bahrain": "bh.indeed.com",
  "China": "cn.indeed.com",
  "Denmark": "dk.indeed.com",
  "Finland": "fi.indeed.com",
  "Greece": "gr.indeed.com",
  "Hong Kong": "hk.indeed.com",
  "Indonesia": "id.indeed.com",
  "Kuwait": "kw.indeed.com",
  "Luxembourg": "lu.indeed.com",
  "Morocco": "ma.indeed.com",
  "Nigeria": "ng.indeed.com",
  "Norway": "no.indeed.com",
  "Oman": "om.indeed.com",
  "Peru": "pe.indeed.com",
  "Saudi Arabia": "sa.indeed.com",
  "Taiwan": "tw.indeed.com",
  "Turkey": "tr.indeed.com",
  "Ukraine": "ua.indeed.com",
  "Netherlands": "nl.indeed.com",
  "Ireland": "ie.indeed.com",
  "Portugal": "pt.indeed.com",
  "France": "fr.indeed.com",
  "Sweden": "se.indeed.com",
  "Estonia": "ee.indeed.com",
  "Czech Republic": "cz.indeed.com",
  "Poland": "pl.indeed.com",
  "Lithuania": "lt.indeed.com",
  "Italy": "it.indeed.com",
  "Belgium": "be.indeed.com",
  "Spain": "es.indeed.com",
  "Switzerland": "ch.indeed.com",
  "Gibraltar": "uk.indeed.com"  

}

# Scrape and analyze jobs
all_jobs = []
index = 0
for country in countries:
    for keyword in keywords:
        country_domain = country_domains.get(country)
        jobs = get_indeed_jobs(keyword , country_domain, country , max_pages)
        all_jobs.extend(jobs)
        time.sleep(2)
    index = index +1
    
# remove duplicates
unique_jobs_data = [dict(t) for t in {tuple(d.items()) for d in all_jobs}]



print(len(unique_jobs_data))
# Save to CSV
if all_jobs:
    save_to_mongodb(all_jobs)
    print(f"Saved {len(all_jobs)} jobs t")
else:
    print("No jobs found.")