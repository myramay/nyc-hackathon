"""Narrow down NYC shelter options from a person's situation.

    from shelters.match import match, Profile
    match(Profile(household="single", age=34, gender="woman", borough="Brooklyn"))

Nothing here is stored: the profile is used for one match and discarded.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import List, Literal, Optional

from pydantic import BaseModel, Field

from shelters.access_points import ACCESS_POINTS

DIRECTORY = Path(__file__).resolve().parent.parent / "data" / "shelters" / "directory.json"

Household = Literal["single", "adult_family", "family_with_children", "youth_alone"]
Gender = Literal["man", "woman", "nonbinary", "unspecified"]
Need = Literal["mental_health", "substance_use", "hiv", "mobility"]
Wants = Literal["bed_tonight", "daytime_help", "not_ready_for_shelter"]


class Profile(BaseModel):
    household: Household = Field(description="single adult; adults with no minor children; family with children under 18; or a young person on their own")
    age: Optional[int] = Field(None, ge=0, le=120, description="age of the person asking (or the head of household)")
    gender: Gender = "unspecified"
    pregnant: bool = False
    fleeing_violence: bool = False
    veteran: bool = False
    lgbtq: bool = False
    employed: bool = False
    has_pet: bool = False
    needs_immigration_help: bool = False
    needs: List[Need] = Field(default_factory=list)
    in_dhs_shelter_last_12_months: bool = False
    at_risk_not_yet_homeless: bool = False
    wants: Wants = "bed_tonight"
    borough: Optional[Literal["Manhattan", "Brooklyn", "Bronx", "Queens", "Staten Island"]] = None
    zip: Optional[str] = None


class Option(BaseModel):
    id: str
    name: str
    kind: str
    why: str                      # why this fits the person
    what: str
    address: Optional[str] = None
    borough: Optional[str] = None
    phone: Optional[str] = None
    hours: Optional[str] = None
    transit: Optional[str] = None
    source: str


class Excluded(BaseModel):
    name: str
    reason: str


class MatchResult(BaseModel):
    first_step: str
    urgent: List[Option]
    go_now: List[Option]
    also_consider: List[Option]
    help_lines: List[Option]
    not_for_you: List[Excluded]
    likely_placements: dict       # shelters from the city directory this person could be assigned to
    rights_and_tips: List[str]


@lru_cache(maxsize=1)
def directory() -> dict:
    return json.loads(DIRECTORY.read_text()) if DIRECTORY.exists() else {"shelters": [], "homebase": [], "sources": {}}


def _opt(ap: dict, why: str) -> Option:
    return Option(id=ap["id"], name=ap["name"], kind=ap["kind"], why=why, what=ap["what"], address=ap.get("address"),
                  borough=ap.get("borough"), phone=ap.get("phone"), hours=ap.get("hours"), transit=ap.get("transit"),
                  source=ap["source"])


def _household(p: Profile) -> str:
    # A minor on their own can't use adult intake; route them to youth services.
    if p.household == "single" and p.age is not None and p.age < 18:
        return "youth_alone"
    return p.household


def _fits(ap: dict, p: Profile, hh: str) -> Optional[str]:
    """None if the access point fits; otherwise the reason it doesn't."""
    s = ap["serves"]
    if hh == "youth_alone" and "household" in s and hh not in s["household"] and "single" in s["household"]:
        return "Adults 18+ only."
    if "household" in s and hh not in s["household"]:
        label = {"single": "single adults", "adult_family": "adult families", "family_with_children": "families with children",
                 "youth_alone": "young people on their own"}
        return "For " + " / ".join(label[h] for h in s["household"]) + " only."
    if p.age is not None:
        if "min_age" in s and p.age < s["min_age"]:
            return f"Ages {s['min_age']}+ only."
        if "max_age" in s and p.age > s["max_age"]:
            return f"Up to age {s['max_age']} only."
    elif "max_age" in s and hh != "youth_alone":
        return f"For young people up to age {s['max_age']}. Add your age to check."
    if "gender" in s and p.gender != "unspecified" and p.gender not in s["gender"]:
        return {"man": "Women only.", "woman": "Men only."}.get(p.gender, "Not for this gender.")
    return None


def match(p: Profile) -> MatchResult:
    hh = _household(p)
    urgent, go_now, also, lines, excluded = [], [], [], [], []
    by_id = {a["id"]: a for a in ACCESS_POINTS}

    # ---- urgent ----
    if p.fleeing_violence:
        urgent.append(_opt(by_id["dv-hotline"], "You said you're fleeing violence. DV shelters are confidential and "
                                                 "placed through this hotline, for you and any children."))
        lines.append(_opt(by_id["sexual-assault"], "If you've been sexually assaulted."))

    # ---- first step ----
    if p.at_risk_not_yet_homeless:
        first = "You still have housing: start with a Homebase office. They help people stay housed (rent arrears, " \
                "landlord mediation, benefits) before shelter is needed."
    elif p.in_dhs_shelter_last_12_months and hh in ("single", "adult_family"):
        first = "You were in a DHS shelter in the last 12 months: go back to that same shelter first. That's DHS's rule."
    elif hh == "youth_alone":
        first = "Adult intake centers are for 18+. Go to a youth program (below), or call 311 and ask for Runaway and " \
                "Homeless Youth services."
    elif p.wants == "not_ready_for_shelter":
        first = "Drop-in centers need no intake: walk in for food, showers, and help. Street outreach (311) can also " \
                "refer you to a Safe Haven, a low-barrier bed."
    else:
        first = {"single": "Go to the intake center for your gender. You'll be assessed and assigned a shelter.",
                 "adult_family": "Go to Adult Family Intake together, with proof of your relationship.",
                 "family_with_children": "Go to PATH in the Bronx with ID for everyone in your family."}[hh]
    if p.fleeing_violence:
        first = "Call the domestic violence hotline first (800-621-4673): it can place you somewhere confidential. " + first

    # ---- homebase (prevention) ----
    if p.at_risk_not_yet_homeless:
        hb = [h for h in directory().get("homebase", []) if p.zip and p.zip in h["zip_codes_served"]] or \
             [h for h in directory().get("homebase", []) if p.borough and h["borough"] == p.borough][:3]
        for h in hb:
            go_now.append(Option(id=h["id"], name=f"Homebase: {h['name']}", kind="homebase",
                                 why="Serves your ZIP code." if p.zip and p.zip in h["zip_codes_served"] else "In your borough.",
                                 what="Homelessness prevention: help keeping your housing.", address=h["address"],
                                 borough=h["borough"], phone=h.get("phone"), source="NYC Open Data ntcm-2w4k"))
        if not hb:
            go_now.append(Option(id="homebase-311", name="Homebase", kind="homebase", why="Homelessness prevention.",
                                 what="Call 311 and ask for the Homebase office for your ZIP code.", phone="311",
                                 source="NYC Open Data ntcm-2w4k"))

    # ---- access points ----
    for ap in ACCESS_POINTS:
        if ap["kind"] == "hotline":
            s = ap["serves"]
            if ap["id"] in ("dv-hotline", "sexual-assault"):
                continue
            if s.get("all") or (s.get("flag") == "veteran" and p.veteran) or \
               (s.get("flag") == "immigration_help" and p.needs_immigration_help) or (s.get("need") in p.needs):
                lines.append(_opt(ap, "Useful for everyone." if s.get("all") else "Matches what you told us."))
            continue
        reason = _fits(ap, p, hh)
        if reason:
            excluded.append(Excluded(name=ap["name"], reason=reason))
            continue
        why = _why(ap, p, hh)
        if ap["kind"] == "intake" and not p.at_risk_not_yet_homeless and p.wants != "not_ready_for_shelter":
            go_now.append(_opt(ap, why))
        elif ap["kind"] in ("youth_shelter", "youth_drop_in") and hh == "youth_alone":
            go_now.append(_opt(ap, why))
        elif ap["kind"] in ("drop_in", "outreach") and p.wants == "not_ready_for_shelter":
            go_now.append(_opt(ap, why))
        elif ap["kind"] == "walk_in_shelter" and p.wants == "bed_tonight" and not p.in_dhs_shelter_last_12_months:
            also.append(_opt(ap, why + " A same-day option if you don't want to go through DHS intake tonight."))
        else:
            also.append(_opt(ap, why))

    # Nearest first when a borough is given.
    for lst in (go_now, also):
        lst.sort(key=lambda o: (0 if not p.borough or o.borough == p.borough else 1))

    return MatchResult(first_step=first, urgent=urgent, go_now=go_now, also_consider=also, help_lines=lines,
                       not_for_you=excluded, likely_placements=_placements(p, hh), rights_and_tips=_tips(p, hh))


def _why(ap: dict, p: Profile, hh: str) -> str:
    bits = []
    if ap["kind"] == "intake":
        bits.append({"single": f"Intake for single {'women' if p.gender == 'woman' else 'men' if p.gender == 'man' else 'adults'}.",
                     "adult_family": "Intake for adult families.", "family_with_children": "Intake for all families with children."}.get(hh, "Intake."))
    elif ap["kind"] in ("youth_shelter", "youth_drop_in"):
        bits.append("For young people your age.")
    elif ap["kind"] == "drop_in":
        bits.append("No intake needed; walk in.")
    elif ap["kind"] == "outreach":
        bits.append("For people on the street who aren't ready for shelter.")
    else:
        bits.append("Open to you.")
    if p.borough and ap.get("borough") == p.borough:
        bits.append(f"In {p.borough}.")
    if set(ap.get("needs", [])) & set(p.needs):
        bits.append("Offers " + " and ".join(n.replace("_", " ") for n in set(ap["needs"]) & set(p.needs)) + " support.")
    return " ".join(bits)


def _placements(p: Profile, hh: str) -> dict:
    d = directory()
    serves = {"single": {"single_adults"}, "adult_family": {"adult_families"}, "family_with_children": {"families_with_children"},
              "youth_alone": set()}[hh]
    if hh == "single" and p.wants == "not_ready_for_shelter":
        serves.add("single_adults_street_homeless")
    rows = [s for s in d.get("shelters", []) if s["serves"] in serves]
    if hh == "single":
        if p.gender == "woman":
            rows = [s for s in rows if "men" not in s["tags_from_name"]]
        elif p.gender == "man":
            rows = [s for s in rows if "women" not in s["tags_from_name"]]

    # Specific needs outrank a gender match: a veteran should see veterans' shelters before generic men's shelters.
    needs = set(p.needs) | ({"veterans"} if p.veteran else set()) | ({"seniors"} if (p.age or 0) >= 50 else set()) | \
        ({"employment"} if p.employed else set()) | ({"lgbtq"} if p.lgbtq else set())
    gender_tag = {"woman": {"women"}, "man": {"men"}}.get(p.gender, set())

    def score(s):
        tags = set(s["tags_from_name"])
        return (2 * len(needs & tags) + len(gender_tag & tags), 1 if p.borough and s["borough"] == p.borough else 0, s["capacity"] or 0)

    rows.sort(key=score, reverse=True)
    by_boro = {}
    for s in rows:
        by_boro[s["borough"]] = by_boro.get(s["borough"], 0) + 1
    src = d.get("sources", {}).get("shelters", {})
    if p.fleeing_violence:
        dv = ("If you're fleeing violence, you'll likely be placed in a confidential domestic violence shelter through "
              "the hotline, not one of these. ")
    else:
        dv = ""
    return {
        "note": dv + ("You can't choose or walk into these: DHS assigns a shelter after intake. This shows the kinds of "
                 "places someone in your situation may be placed. Addresses aren't published by the city.")
                if hh != "youth_alone" else "DHS shelters are for adults 18+ and families. Young people on their own use youth programs.",
        "total_matching": len(rows),
        "by_borough": by_boro,
        "top": [{k: s[k] for k in ("name", "provider", "facility_type", "borough", "capacity", "tags_from_name")} for s in rows[:12]],
        "source": src.get("dataset"), "as_of": src.get("as_of"),
        "tags_note": "Tags like 'women' or 'veterans' are read from the shelter's name, not an official field.",
    }


def _tips(p: Profile, hh: str) -> List[str]:
    t = []
    if hh == "single":
        t.append("ID helps at single-adult intake but isn't required (driver's license, state ID, passport, Social Security or Medicaid card).")
    if hh == "family_with_children":
        t.append("DHS may place your family for up to 10 days while it checks eligibility. If you're found ineligible, you have "
                 "60 days to request a Fair Hearing. Legal Aid (800-649-9125) can help.")
    if hh == "adult_family":
        t.append("Adult families must prove the relationship (original marriage or domestic-partnership certificate, or documents "
                 "showing a family, caretaking, or medical-dependence relationship) and that you lived together 180 days in the past year.")
    if p.gender in ("nonbinary", "unspecified") or p.lgbtq:
        t.append("Under the NYC Human Rights Law you can use single-sex facilities, including shelter, that match your gender "
                 "identity. If intake refuses, contact the NYC Commission on Human Rights (311).")
    if p.pregnant and hh == "single":
        t.append("If you're pregnant, ask 311 whether to apply at PATH (family intake) or single women's intake.")
    if p.has_pet:
        t.append("Tell intake about your pet. Most placements can't take pets; in 2022, 73 of 31,498 DHS applicants had a pet "
                 "and 26 of them chose to skip shelter because of it (NYC Open Data 5nux-zfmw). Line up family or friends to "
                 "keep your pet if you can.")
    if p.veteran:
        t.append("Veterans go through regular DHS intake, then the Veterans Services Unit refers them to veteran housing.")
    if "mobility" in p.needs:
        t.append("Ask intake for a reasonable accommodation (accessible room, elevator, bathroom) for a disability.")
    t.append("Denied shelter or having problems? Legal Aid's Homeless Rights Project: 800-649-9125. Street outreach: 311, 24/7.")
    return t
