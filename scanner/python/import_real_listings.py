import csv
import json

from pathlib import Path
from datetime import datetime, timezone

CURRENT_DIR = Path(__file__).parent

INPUT_FILE = CURRENT_DIR / "data" / "august_2026.csv"
OUTPUT_FILE = CURRENT_DIR / "real_listings.json"

MAX_LISTINGS = 5


def main():

    listings = []

    with open(INPUT_FILE, newline="", encoding="utf-8-sig") as file:

        reader = csv.DictReader(file)

        for row in reader:

            url = row.get("url")

            if not url:
                continue

            listing = {
                "source": "firstmover_open_data",
                "source_id": row.get("id"),
                "url": row.get("url"),
                "address": row.get("street"),
                "unit": row.get("unit"),
                "neighborhood": row.get("neighborhood"),
                "borough": row.get("borough"),
                "zip_code": row.get("zip_code"),
                "monthly_rent": row.get("price"),
                "net_effective_price": row.get("net_effective_price"),
                "bedrooms": row.get("bedrooms"),
                "available_date": row.get("available_date"),
                "source_group": row.get("source_group"),
                "source_type": row.get("source_type"),
                "discovered_at": datetime.now(timezone.utc).isoformat(),
                "description_available": False
            }

            listings.append(listing)

            if len(listings) >= MAX_LISTINGS:
                break

    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        json.dump(listings, file, indent=4)

    print(f"Imported {len(listings)} genuine rental records!")


if __name__ == "__main__":
    main()
