import asyncio
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

async def get_indeed_jobs_playwright(query, country_domain, country, pages):
    query = query.replace(" ", "+")
    results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # set True to hide browser
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
            locale="en-US",
            timezone_id="Europe/Paris"
        )
        page = await context.new_page()

        for page_num in range(pages):
            url = f"https://{country_domain}/jobs?q={query}&start={page_num * 10}"
            print(f"\nFetching: {url}")
            try:
                await page.goto(url, timeout=60000)
                await page.wait_for_selector(".job_seen_beacon", timeout=15000)
                html = await page.content()
                soup = BeautifulSoup(html, "html.parser")
            except Exception as e:
                print(f"❌ Failed to load page {page_num + 1}: {e}")
                continue

            job_cards = soup.select(".job_seen_beacon")
            print(f"✅ Found {len(job_cards)} job cards")

            for card in job_cards:
                try:
                    title_tag = card.find("h2")
                    title = title_tag.get_text(strip=True) if title_tag else None

                    company_tag = card.find("span", class_="companyName")
                    company = company_tag.get_text(strip=True) if company_tag else None

                    location_tag = card.find("div", class_="companyLocation")
                    location = location_tag.get_text(strip=True) if location_tag else None

                    job_id = card.get("data-jk")
                    job_url = f"https://{country_domain}/viewjob?jk={job_id}" if job_id else None

                    easy_apply = bool(card.find("span", {"data-testid": "indeedApply"}))

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
                    print(f"⚠️ Error parsing job card: {e}")
                    continue

        await browser.close()

    return results


# Run the scraper
if __name__ == "__main__":
    async def main():
        jobs = await get_indeed_jobs_playwright(
            query="remote python",
            country_domain="fr.indeed.com",
            country="France",
            pages=2
        )
        print("\n🎯 Sample jobs:\n")
        for job in jobs[:3]:
            print(job)

    asyncio.run(main())
