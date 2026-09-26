import argparse
import json
import os
import sys
import requests

from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urlparse


HERE = Path(__file__).parent
OUTPUT = HERE / "listings.json"


def load_feed(args):
    if args.feed_file:
        with open(args.feed_file, encoding="utf-8") as file:
            return json.load(file)

    url = args.feed_url or os.getenv("LISTING_FEED_URL")

    if not url:
        raise ValueError(
            "Provide --feed-file or configure LISTING_FEED_URL"
        )

    headers = {}
    token = os.getenv("LISTING_FEED_API_KEY")

    if token:
        headers["Authorization"] = f"Bearer {token}"

    response = requests.get(
        url,
        headers=headers,
        timeout=30
    )
    response.raise_for_status()
    return response.json()


def normalize(records):
    if not isinstance(records, list):
        raise ValueError("Expected a JSON array of listings")

    listings = []
    seen = set()
    now = datetime.now(timezone.utc).isoformat()

    for record in records:
        if not isinstance(record, dict):
            continue

        url = str(record.get("url") or "").strip()
        text = str(
            record.get("text")
            or record.get("description")
            or ""
        ).strip()

        source = str(record.get("source") or "rental_feed")

        parsed = urlparse(url)

        if parsed.scheme not in ("http", "https"):
            continue

        if not text:
            continue

        if url in seen:
            continue

        seen.add(url)

        listings.append({
            "source": source,
            "url": url,
            "text": text,
            "discovered_at": now
        })

    return listings


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--feed-file")
    parser.add_argument("--feed-url")

    args = parser.parse_args()

    try:
        records = load_feed(args)
        listings = normalize(records)

        # Write only after successful retrieval and validation.
        temporary = OUTPUT.with_suffix(".tmp")

        temporary.write_text(
            json.dumps(listings, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

        temporary.replace(OUTPUT)

        print(f"Discovered {len(listings)} valid listings.")

    except Exception as error:
        print(f"Discovery failed: {error}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
