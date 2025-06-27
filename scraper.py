from pymongo import MongoClient
import requests
from bs4 import BeautifulSoup
import time , os


CRAWLBASE_TOKEN = os.getenv("CRAWLBASE_TOKEN")
mongo_uri = os.getenv("MONGODB_URI")

def get_indeed_jobs(query, country_domain, country ,pages):
    query = query.replace(" ", "+")
    results = []
    for page in range(0,pages):
        url = f"https://{country_domain}/jobs?q={query}&start={page * 10}"
        print(url)
        response = requests.get(
                    f"https://api.crawlbase.com/?token={CRAWLBASE_TOKEN}&url={url}"
                )
        soup = BeautifulSoup(response.text, "html.parser")
    
        jobs_container = soup.find("div", id="mosaic-provider-jobcards")
        job_cards = jobs_container.find_all("li") if jobs_container else []
        print(f"Len cards {len(job_cards)}")
        
        for card in job_cards:
            title_tag = card.find("h2")
            id_tag = card.find("a").get("id").replace("job_", "") if title_tag else None
            link_tag = title_tag.find("a") if title_tag else None

            
            company_tag =    card.find("span", attrs={"data-testid": "company-name"})
            location_tag =   card.find("div",  attrs={"data-testid": "text-location"})
            easy_apply = True if card.find("span", {"data-testid": "indeedApply"}) else False

    
            title = title_tag.text.strip() if title_tag else None
            company = company_tag.text.strip() if company_tag else None
            location = location_tag.text.strip() if location_tag else None
            
            
            job_url = f"https://{country_domain}/viewjob?jk={id_tag}"


    
            if title:
                results.append({
                    "title": title,
                    "company": company,
                    "location": location ,
                    "country": country.upper(),
                    "job_url": job_url,
                    "easy_apply": easy_apply
                })
    
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
countries = [
    "USA"                
]

#keywords = ["remote " + skill for skill in skills]
keywords = [
    "data analyst"
]
max_pages = 5
output_file = "indeed_jobs_analyzed_(12-18).csv"

# Indeed country-specific domains
country_domains = {
  "USA": "www.indeed.com",
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