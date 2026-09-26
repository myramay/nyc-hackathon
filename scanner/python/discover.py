import argparse
import json
import requests

from pathlib import Path
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse


OUTPUT_FILE = Path(__file__).parent / "listings.json"


# -----------------------------------------
# Fetch a website
# -----------------------------------------

def fetch_page(url):

    response = requests.get(
        url,
        headers={
            "User-Agent": "DivHacks2026/1.0 (housing research)"
        },
        timeout=15
    )

    response.raise_for_status()

    return response.text


# -----------------------------------------
# Extract listing URLs
# -----------------------------------------

def extract_listings(html, base_url, selector, source):

    soup = BeautifulSoup(html, "html.parser")

    listings = []

    cards = soup.select(selector)

    for card in cards:

        href = card.get("href")

        if not href:
            continue

        listing_url = urljoin(base_url, href)

        # Only accept HTTP/HTTPS links from the selected website.
        parsed = urlparse(listing_url)
        base = urlparse(base_url)

        if parsed.scheme not in ("http", "https"):
            continue

        if parsed.hostname != base.hostname:
            continue

        listing_url = parsed._replace(fragment="").geturl()

        listings.append({
            "source": source,
            "url": listing_url,
            "discovered_at": datetime.now(
                timezone.utc
            ).isoformat()
        })

    return listings


# -----------------------------------------
# Remove duplicates
# -----------------------------------------

def remove_duplicates(listings):

    seen = set()
    unique = []

    for listing in listings:

        url = listing["url"]

        if url not in seen:

            seen.add(url)

            unique.append(listing)

    return unique


# -----------------------------------------
# Save JSON
# -----------------------------------------

def save_listings(listings):

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            listings,
            file,
            indent=4,
            ensure_ascii=False
        )

    print(f"Saved {len(listings)} listings to {OUTPUT_FILE}")


# -----------------------------------------
# Main
# -----------------------------------------

def main():

    parser = argparse.ArgumentParser()

    parser.add_argument("--search-url")

    parser.add_argument("--selector", default="a.listing-card")

    parser.add_argument("--source", default="test")

    parser.add_argument("--sample", action="store_true")

    args = parser.parse_args()

    print("Starting rental listing discovery...")

    if args.sample:

        sample_file = Path(__file__).parent / "sample.html"

        html = sample_file.read_text(encoding="utf-8")

        base_url = "https://example.com"

    else:

        if not args.search_url:
            parser.error("--search-url is required without --sample")

        base_url = args.search_url

        html = fetch_page(base_url)

    listings = extract_listings(
        html,
        base_url,
        args.selector,
        args.source
    )

    listings = remove_duplicates(listings)

    if not listings:
        print("No listings found. Check the HTML selector.")
        return

    save_listings(listings)

    print("Discovery completed!")


if __name__ == "__main__":
    main()
