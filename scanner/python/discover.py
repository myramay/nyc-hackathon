
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timezone
from urllib.parse import urljoin


# -----------------------------------------
# Configuration
# -----------------------------------------

BASE_URL = "https://example.com"

SEARCH_URL = "https://example.com/apartments"

OUTPUT_FILE = "listings.json"


# -----------------------------------------
# Step 1: Fetch the search page
# -----------------------------------------

def fetch_page(url):

    response = requests.get(url, timeout=15)

    response.raise_for_status()

    return response.text


# -----------------------------------------
# Step 2: Extract listing URLs
# -----------------------------------------

def extract_listings(html):

    soup = BeautifulSoup(html, "html.parser")

    listings = []

    # TODO: Replace this selector after inspecting
    # the actual rental website's HTML.

    cards = soup.select("a.listing-card")

    for card in cards:

        href = card.get("href")

        if not href:
            continue

        listing_url = urljoin(BASE_URL, href)

        listing = {
            "source": "example",
            "url": listing_url,
            "discovered_at": datetime.now(timezone.utc).isoformat()
        }

        listings.append(listing)

    return listings


# -----------------------------------------
# Step 3: Remove duplicate URLs
# -----------------------------------------

def remove_duplicates(listings):

    seen = set()
    unique_listings = []

    for listing in listings:

        url = listing["url"]

        if url not in seen:
            seen.add(url)
            unique_listings.append(listing)

    return unique_listings


# -----------------------------------------
# Step 4: Save listings to JSON
# -----------------------------------------

def save_listings(listings):

    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:

        json.dump(listings, file, indent=4)

    print(f"Saved {len(listings)} listings to {OUTPUT_FILE}")


# -----------------------------------------
# Main
# -----------------------------------------


def main():

    print("Starting rental listing discovery...")

    # Temporarily read local HTML instead of requesting a website.
    with open("sample.html", "r", encoding="utf-8") as file:
        html = file.read()

    listings = extract_listings(html)

    listings = remove_duplicates(listings)

    save_listings(listings)

    print("Discovery completed!")


if __name__ == "__main__":
    main()
