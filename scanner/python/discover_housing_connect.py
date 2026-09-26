import requests
import json

from pathlib import Path
from datetime import datetime, timezone


# Official NYC Open Data dataset
API_URL = "https://data.cityofnewyork.us/resource/vy5i-a666.json"

OUTPUT_FILE = Path(__file__).parent / "housing_opportunities.json"


# Step 1: Fetch actual housing records
def fetch_opportunities():

    params = {
        "$limit": 10,
        "$order": "lottery_id DESC"
    }

    response = requests.get(
        API_URL,
        params=params,
        timeout=20
    )

    response.raise_for_status()

    return response.json()


# Step 2: Normalize the records
def normalize_opportunities(records):

    opportunities = []

    for record in records:

        opportunity = {
            "source": "nyc_housing_connect",
            "source_id": record.get("lottery_id"),
            "title": record.get("lottery_name"),
            "source_url": "https://data.cityofnewyork.us/d/vy5i-a666",
            "discovered_at": datetime.now(timezone.utc).isoformat(),
            "raw_data": record
        }

        opportunities.append(opportunity)

    return opportunities


# Step 3: Save the results
def save_opportunities(opportunities):

    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        json.dump(opportunities, file, indent=4, ensure_ascii=False)

    print(f"Saved {len(opportunities)} housing records!")


# Main program
def main():

    print("Fetching NYC housing opportunities...")

    try:
        records = fetch_opportunities()

        if not records:
            print("No records returned.")
            return

        print("Available dataset fields:", list(records[0].keys()))

        opportunities = normalize_opportunities(records)

        save_opportunities(opportunities)

    except requests.RequestException as error:
        print(f"Request failed: {error}")


if __name__ == "__main__":
    main()
