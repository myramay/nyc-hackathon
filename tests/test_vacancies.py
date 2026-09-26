"""python -m unittest discover tests   (offline: lotteries come from a fixture, not the network)"""
import json
import tempfile
import unittest
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

from vacancies import feed

FUTURE = (date.today() + timedelta(days=5)).isoformat()
PAST = (date.today() - timedelta(days=2)).isoformat()


def unit(layout, rent, lo, hi, incomes):
    return {"unitLayoutTypeName": layout, "actualRent": rent, "minimumHouseholdSize": lo, "maximumHouseholdSize": hi,
            "unitRegulatoryMechanismAmi": 60, "unitIncome": [{"houseHoldSize": s, "minimumIncome": a, "maximumIncome": b} for s, a, b in incomes]}


FIXTURE = {"source": "housing_connect", "fetched_at": datetime.now(timezone.utc).isoformat(), "lotteries": [
    {"summary": {"lotteryId": 1, "lotteryName": "Open Bronx", "borough": "Bronx", "units": 2, "endIn": 5},
     "ad": {"lotteryName": "Open Bronx", "endDate": FUTURE, "lotteryBuildings": [{"address": "1 Test Ave", "zip": "10451"}],
            "units": [unit("1 Bedroom", 2000, 1, 3, [(3, 60000, 90000)]), unit("2 Bedroom", 3200, 2, 5, [(3, 70000, 110000)])]}},
    {"summary": {"lotteryId": 2, "lotteryName": "Closed", "borough": "Queens", "units": 1, "endIn": 0},
     "ad": {"lotteryName": "Closed", "endDate": PAST, "lotteryBuildings": [], "units": [unit("Studio", 1500, 1, 2, [])]}},
]}
LISTINGS = [
    {"source": "test", "url": "u1", "text": "2 bedroom apartment in Queens. Rent $2400/month. No vouchers accepted."},
    {"source": "test", "url": "u2", "text": "One bedroom apartment. $2100/month. Section 8 welcome."},
    {"source": "test", "url": "u3", "text": "Studio apartment. $1900/month. Applicants must earn 40x monthly rent."},
]


class Feed(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        cache, lst = Path(self.tmp.name) / "lotteries.json", Path(self.tmp.name) / "listings.json"
        cache.write_text(json.dumps(FIXTURE))
        lst.write_text(json.dumps(LISTINGS))
        self.p = [mock.patch.object(feed, "CACHE", cache), mock.patch.object(feed, "LISTING_FILES", [lst])]
        for p in self.p:
            p.start()
        feed._cache.clear()

    def tearDown(self):
        for p in self.p:
            p.stop()
        self.tmp.cleanup()

    def test_only_open_lotteries(self):
        f = feed.build_feed()
        self.assertEqual([i.title for i in f.items if i.kind == "lottery"], ["Open Bronx"])

    def test_discriminatory_listings_hidden(self):
        f = feed.build_feed()
        self.assertEqual(f.hidden["discriminatory"], 2)
        self.assertEqual([i.url for i in f.items if i.kind == "listing"], ["u2"])

    def test_voucher_waives_minimum_income(self):
        self.assertEqual(feed.build_feed(household_size=3, income=30000, has_voucher=True).counts["lotteries"], 1)
        self.assertEqual(feed.build_feed(household_size=3, income=30000, has_voucher=False).counts["lotteries"], 0)

    def test_income_over_max_excluded_even_with_voucher(self):
        self.assertEqual(feed.build_feed(household_size=3, income=150000).counts["lotteries"], 0)

    def test_voucher_limit_filters_unit_offers(self):
        f = feed.build_feed(within_voucher_limit=True, kind="lottery")
        offers = f.items[0].unit_offers
        self.assertEqual([u["layout"] for u in offers], ["1 Bedroom"])     # $3,200 2BR is over the limit
        self.assertTrue(offers[0]["rent_within_voucher_limit"])

    def test_household_size_filters(self):
        f = feed.build_feed(household_size=5, kind="lottery")
        self.assertEqual([u["layout"] for u in f.items[0].unit_offers], ["2 Bedroom"])

    def test_welcoming_listing_ranks_first(self):
        self.assertEqual(feed.build_feed().items[0].url, "u2")


if __name__ == "__main__":
    unittest.main()
