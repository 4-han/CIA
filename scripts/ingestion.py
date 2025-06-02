import argparse
import requests
from bs4 import BeautifulSoup
from tqdm.auto import tqdm
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import os
import re
import json
from datetime import datetime

parser = argparse.ArgumentParser(description="Scrape PDF links from NITW notifications page.")
parser.add_argument(
    "--click_workshop", 
    type=bool, 
    default=False, 
    help="Whether to click on the 'Workshops' tab (True/False). Default is False."
)
parser.add_argument(
    "--start_date", 
    type=str, 
    default="2025-05-01", 
    help="The start date for scraping (format: YYYY-MM-DD). Default is 2025-05-01."
)
parser.add_argument(
    "--end_date", 
    type=str, 
    default="2025-05-31", 
    help="The end date for scraping (format: YYYY-MM-DD). Default is 2025-05-31."
)

args = parser.parse_args()

click_workshop = args.click_workshop
START_DATE = datetime.strptime(args.start_date, "%Y-%m-%d")
END_DATE = datetime.strptime(args.end_date, "%Y-%m-%d")


URL = "https://www.nitw.ac.in/notifications"
LINKS_FILE = "../data/pdf_links.json"
os.makedirs(os.path.dirname(LINKS_FILE), exist_ok=True)

print("[INFO] Launching headless Chrome browser...")
options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

print(f"[INFO] Connecting to {URL}...")
driver.get(URL)
print("[INFO] Waiting for JavaScript content to render...")
time.sleep(5)


print("[INFO] Loading previously saved PDF entries...")
if os.path.exists(LINKS_FILE):
    with open(LINKS_FILE, "r") as f:
        saved_links = json.load(f)
else:
    saved_links = []

saved_urls = {entry["url"] for entry in saved_links}
all_pdf_data = saved_links[:]
new_data = []


def extract_pdf_data(soup, known_urls):
    results = []
    cards = soup.select("div.MuiGrid-root.MuiGrid-container.MuiGrid-item")

    for card in cards:
        link_tag = card.find("a", href=lambda href: href and href.endswith(".pdf"))
        date_tag = card.select_one("p.MuiTypography-root.MuiTypography-body1.css-14swc86")
        title_parts = card.select("h5, h6")

        if link_tag and date_tag:
            try:
                link = link_tag["href"]
                date_str = date_tag.text.strip()
                title = " | ".join(part.text.strip() for part in title_parts) if title_parts else "No Title Found"

                match = re.search(r"\d{4}-\d{2}-\d{2}", date_str)
                if not match:
                    continue

                date_obj = datetime.strptime(match.group(), "%Y-%m-%d")

                if START_DATE <= date_obj <= END_DATE and link not in known_urls:
                    results.append({
                        "url": link,
                        "date": date_obj.strftime("%Y-%m-%d"),
                        "title": title
                    })
            except Exception as e:
                print("[ERROR] Skipping a card due to issue:", e)
    return results


print("[INFO] Parsing initial/default page content...")
initial_soup = BeautifulSoup(driver.page_source, "html.parser")
initial_data = extract_pdf_data(initial_soup, saved_urls)
all_pdf_data.extend(initial_data)
new_data.extend(initial_data)
saved_urls.update(entry["url"] for entry in initial_data)


if click_workshop:
    print("[INFO] Attempting to click on the workshops tab...")
    wait = WebDriverWait(driver, 10)
    try:
        workshop_elem = wait.until(EC.element_to_be_clickable((
            By.CSS_SELECTOR,
            "#root > div > div.MuiGrid-root.MuiGrid-container.MuiGrid-direction-xs-column.MuiGrid-grid-xs-10.MuiGrid-grid-md-8.css-uh8tfv > div:nth-child(3) > div:nth-child(2) > h4"
        )))
        driver.execute_script("arguments[0].click();", workshop_elem)
        time.sleep(3)
    
        print("[INFO] Parsing page after clicking Workshops...")
        workshop_soup = BeautifulSoup(driver.page_source, "html.parser")
        workshop_data = extract_pdf_data(workshop_soup, saved_urls)
        all_pdf_data.extend(workshop_data)
        new_data.extend(workshop_data)
    
    except Exception as e:
        print("[WARN] Could not click the workshop tab:", e)

driver.quit()

if new_data:
    print(f"[SUCCESS] Found {len(new_data)} new PDF link(s) within date range:")
    for entry in new_data:
        print(f" - {entry['date']} | {entry['title']} | {entry['url']}")
else:
    print("[INFO] No new PDF links found in the specified date range.")

with open(LINKS_FILE, "w") as f:
    json.dump(all_pdf_data, f, indent=2)

print("[INFO] Updated PDF link list saved to", LINKS_FILE)
