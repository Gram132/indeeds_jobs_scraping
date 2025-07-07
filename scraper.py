import requests
from pymongo import MongoClient
import time
from itertools import cycle
import os 

SERPER_API_KEYS = os.getenv("SERPER_API_KEYS", "").split(",")
serper_key_cycle = cycle(SERPER_API_KEYS)
mongo_uri = os.getenv("MONGODB_URI")


def get_jobs_for_query_country(query, country_domain, country_code, pages=2, new=True):
    all_jobs = []

    for page in range(pages):
        # Build search query
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
                    break  # Exit retry loop
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

        # Parse results
        if not organic:
            print(f"❌ No results on page {page + 1} for '{query}' in {country_code}")
            continue

        print(f"✅ {country_code.upper()} Page {page + 1}: Found {len(organic)} results for '{query}'")

        for result in organic:
            link = result.get("link", "").strip()
            title = result.get("title", "").strip()

            if f"{country_domain}/jobs" in link:
                all_jobs.append({
                    "title": title,
                    "job_url": link,
                    "location": None,  # Optional: add scraping if needed
                    "is_new": new,
                    "country": country_code.upper()
                })
                print(f"→ {title} | {link}")

        time.sleep(1)  # Respect rate limits

    return all_jobs


def save_to_mongodb(data, db_name="Indeed_jobs_urls", collection_name="Indeed_data", uri=mongo_uri):
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

    country_data = {
        "us": {
            "country": "United States",
            "domain": "indeed.com",
            "keywords": keywords_5
        },
        "ca": {
            "country": "Canada",
            "domain": "ca.indeed.com",
            "keywords": keywords_5
        },
        "fr": {
            "country": "France",
            "domain": "fr.indeed.com",
            "keywords": keywords_5
        },
        "es": {
            "country": "Spain",
            "domain": "es.indeed.com",
            "keywords": keywords_5
        },
        "it": {
            "country": "Italy",
            "domain": "it.indeed.com",
            "keywords": keywords_5
        },
        "ch": {
            "country": "Switzerland",
            "domain": "ch.indeed.com",
            "keywords": keywords_5
        },
        "be": {
            "country": "Belgium",
            "domain": "be.indeed.com",
            "keywords": keywords_5
        },
        "pt": {
            "country": "Portugal",
            "domain": "pt.indeed.com",
            "keywords": keywords_5
        },
        "se": {
            "country": "Sweden",
            "domain": "se.indeed.com",
            "keywords": keywords_5
        },
        "de": {
            "country": "Germany",
            "domain": "de.indeed.com",
            "keywords": keywords_5
        },
        "nl": {
            "country": "Netherlands",
            "domain": "nl.indeed.com",
            "keywords": keywords_5
        },
        "uk": {
            "country": "United Kingdom",
            "domain": "uk.indeed.com",
            "keywords": keywords_5
        },
        "ie": {
            "country": "Ireland",
            "domain": "ie.indeed.com",
            "keywords": keywords_5
        },
        "au": {
            "country": "Australia",
            "domain": "au.indeed.com",
            "keywords": keywords_5
        },
        "ae": {
            "country": "United Arab Emirates",
            "domain": "ae.indeed.com",
            "keywords": keywords_5
        }
     
    }


    all_results = []

    for country_code, data in country_data.items():
        domain = data["domain"]
        keywords = data["keywords"]

        for keyword in keywords:
            print(f"\n🔎 Searching '{keyword}' in {country_code.upper()}")
            jobs = get_jobs_for_query_country(
                keyword, domain, country_code, pages=3, new=True
            )
            all_results.extend(jobs)
        
    print(f"\n🎯 Total jobs scraped: {len(all_results)}")
    save_to_mongodb(all_results)

