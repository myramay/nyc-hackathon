"""python -m unittest discover tests"""
import unittest

from shelters.match import Profile, match


def ids(opts):
    return [o.id for o in opts]


class ShelterMatch(unittest.TestCase):
    def test_single_woman_gets_womens_intake_not_mens(self):
        r = match(Profile(household="single", age=34, gender="woman"))
        self.assertIn("intake-women-help", ids(r.go_now))
        self.assertIn("intake-women-franklin", ids(r.go_now))
        self.assertNotIn("intake-men", ids(r.go_now))
        self.assertTrue(any(e.name.startswith("Single Adult Intake") and e.reason == "Men only." for e in r.not_for_you))

    def test_womens_placements_exclude_mens_shelters(self):
        r = match(Profile(household="single", age=34, gender="woman"))
        self.assertTrue(r.likely_placements["total_matching"] > 0)
        self.assertFalse(any("men" in s["tags_from_name"] for s in r.likely_placements["top"]))

    def test_minor_alone_goes_to_youth_not_adult_intake(self):
        r = match(Profile(household="single", age=17))
        self.assertEqual(set(ids(r.go_now)), {"covenant-house", "the-door"})
        self.assertIn("18+", r.first_step)
        self.assertEqual(r.likely_placements["total_matching"], 0)

    def test_family_goes_to_path(self):
        r = match(Profile(household="family_with_children", age=30))
        self.assertEqual(ids(r.go_now), ["intake-path"])

    def test_dv_hotline_is_urgent_and_first(self):
        r = match(Profile(household="family_with_children", age=30, fleeing_violence=True))
        self.assertEqual(ids(r.urgent), ["dv-hotline"])
        self.assertIn("800-621-4673", r.first_step)
        self.assertIn("confidential", r.likely_placements["note"])

    def test_nonbinary_can_use_any_single_intake(self):
        r = match(Profile(household="single", age=30, gender="nonbinary"))
        self.assertTrue({"intake-men", "intake-women-help", "intake-women-franklin"} <= set(ids(r.go_now)))
        self.assertTrue(any("gender identity" in t for t in r.rights_and_tips))

    def test_returning_within_12_months(self):
        r = match(Profile(household="single", age=40, gender="man", in_dhs_shelter_last_12_months=True))
        self.assertIn("same shelter", r.first_step)

    def test_street_homeless_gets_drop_ins_and_safe_haven_route(self):
        r = match(Profile(household="single", age=50, gender="man", wants="not_ready_for_shelter", borough="Bronx"))
        self.assertEqual(r.go_now[0].id, "living-room")          # nearest drop-in first
        self.assertIn("safe-haven-outreach", ids(r.go_now))

    def test_veteran_sees_veteran_shelters_and_va(self):
        r = match(Profile(household="single", age=45, gender="man", veteran=True))
        self.assertIn("veterans", r.likely_placements["top"][0]["tags_from_name"])
        self.assertIn("va", ids(r.help_lines))

    def test_at_risk_gets_homebase_by_zip(self):
        r = match(Profile(household="family_with_children", at_risk_not_yet_homeless=True, zip="10474"))
        self.assertTrue(r.go_now and r.go_now[0].kind == "homebase")
        self.assertIn("Homebase", r.first_step)

    def test_youth_programs_need_age(self):
        r = match(Profile(household="family_with_children"))
        self.assertNotIn("covenant-house", ids(r.also_consider))

    def test_every_access_point_names_a_source(self):
        from shelters.access_points import ACCESS_POINTS
        self.assertTrue(all(a.get("source") for a in ACCESS_POINTS))


if __name__ == "__main__":
    unittest.main()
