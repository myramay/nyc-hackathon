"""Places a person can actually go or call, with who each one serves.

Every entry names its source. Checked 2026-09-26 against:
  DHS  = nyc.gov/site/dhs (single-adults-applying, families-with-children-applying, adult-families, veterans-shelter pages)
  NCS  = Neighborhood Coalition for Shelter Street Sheets, April 2024 (ncsinc.org/get-info)
  ODP  = NYC Open Data, Directory of Homeless Drop-In Centers (bmxf-3rd4)
  BW   = bronxworks.org adult shelter services page
  CAMBA = camba.org drop-in center page
Where sources disagreed, the official DHS page wins (e.g. men's intake moved to 8 E. 3rd St;
NCS's April 2024 sheet still lists 30th St).
"""

ACCESS_POINTS = [
    # ---------------- DHS intake: the front doors to the shelter system ----------------
    {"id": "intake-men", "kind": "intake", "name": "Single Adult Intake Center (men)",
     "address": "8 E. 3rd Street, New York, NY 10003", "borough": "Manhattan", "phone": "311",
     "hours": "Call 311 to confirm hours",
     "serves": {"household": ["single"], "gender": ["man", "nonbinary"], "min_age": 18},
     "what": "Where single adult men apply for DHS shelter. You're assessed, then assigned a shelter.",
     "source": "DHS"},
    {"id": "intake-women-franklin", "kind": "intake", "name": "Franklin Shelter (women's intake)",
     "address": "1122 Franklin Avenue (near E. 166th St.), Bronx, NY", "borough": "Bronx", "phone": "311",
     "hours": "24/7", "transit": "2, 4, 5 to 149th St., then #55 bus to 166th St. & 3rd Ave.",
     "serves": {"household": ["single"], "gender": ["woman", "nonbinary"], "min_age": 18},
     "what": "Where single adult women apply for DHS shelter (no children).", "source": "DHS, NCS"},
    {"id": "intake-women-help", "kind": "intake", "name": "HELP Women's Center (women's intake)",
     "address": "114 Snediker Avenue, Brooklyn, NY", "borough": "Brooklyn", "phone": "311",
     "hours": "24/7", "transit": "C to Liberty Ave.",
     "serves": {"household": ["single"], "gender": ["woman", "nonbinary"], "min_age": 18},
     "what": "Where single adult women apply for DHS shelter (no children).", "source": "DHS, NCS"},
    {"id": "intake-path", "kind": "intake", "name": "PATH (Prevention Assistance and Temporary Housing)",
     "address": "151 E. 151st Street (corner of Walton Ave.), Bronx, NY", "borough": "Bronx", "phone": "718-503-6400",
     "hours": "Open 24 hours; applications during business hours (9am–5pm)", "transit": "2, 4, 5 to 149th St.",
     "serves": {"household": ["family_with_children"]},
     "what": "Where every family with children (ages 0–17) applies. Families may get a temporary placement for up to "
             "10 days while DHS checks eligibility; if found ineligible, you have 60 days to request a Fair Hearing. "
             "Bring ID for everyone in the household (photo ID, birth certificates, Social Security or Medicaid cards).",
     "source": "DHS, NCS"},
    {"id": "intake-adult-family", "kind": "intake", "name": "Adult Family Intake (30th Street)",
     "address": "400 E. 30th Street (at 1st Ave.), Manhattan", "borough": "Manhattan", "phone": "311",
     "hours": "24/7", "transit": "6 to 28th St.",
     "serves": {"household": ["adult_family"], "min_age": 18},
     "what": "Where adult families with no minor children apply: married or domestic-partner couples (bring the original "
             "certificate), or adults with a documented family or caretaking relationship or medical dependence. You must "
             "show you lived together for 180 days in the past year.",
     "source": "DHS (definition), NCS (address; confirm with 311)"},

    # ---------------- Walk-in shelter (not DHS) ----------------
    {"id": "bowery-mission", "kind": "walk_in_shelter", "name": "Bowery Mission, Tribeca Campus",
     "address": "90 Lafayette Street (btwn Walker & White), Manhattan", "borough": "Manhattan", "phone": "212-226-6214",
     "hours": "Intake daily: women 3–3:30pm, men 3:30–5pm. First come, first served.",
     "serves": {"household": ["single"], "gender": ["man", "woman", "nonbinary"], "min_age": 18},
     "what": "Walk in or call. Stay up to 7 nights; meals, showers, clothes, case management, medical referrals, "
             "mental health and detox programs. Waitlist after 7 days.",
     "needs": ["mental_health", "substance_use"], "source": "NCS"},

    # ---------------- Youth ----------------
    {"id": "covenant-house", "kind": "youth_shelter", "name": "Covenant House",
     "address": "460 W. 41st Street (at 10th Ave.), Manhattan", "borough": "Manhattan", "phone": "212-613-0300",
     "hours": "24/7. Call for bed availability.",
     "serves": {"household": ["single", "youth_alone", "family_with_children"], "max_age": 21},
     "what": "Shelter for young people up to age 21, with health care, GED help, and meals.", "source": "NCS"},
    {"id": "the-door", "kind": "youth_drop_in", "name": "The Door",
     "address": "555 Broome Street (at 6th Ave.), Manhattan", "borough": "Manhattan", "phone": "212-941-9090",
     "hours": "Mon–Fri 9am–6pm; food pantry Sat 12–6pm",
     "serves": {"household": ["single", "youth_alone", "family_with_children"], "min_age": 12, "max_age": 24},
     "what": "Ages 12–24. Referrals to NYC shelters, counseling, health and dental care, legal services, education, jobs.",
     "source": "NCS"},

    # ---------------- Drop-in centers (no intake needed; single adults 18+) ----------------
    {"id": "mainchance", "kind": "drop_in", "name": "Mainchance Drop-in Center (Grand Central Neighborhood)",
     "address": "120 E. 32nd Street (btwn Lexington & Park), Manhattan", "borough": "Manhattan", "phone": "212-883-0680",
     "hours": "24 hours, including holidays",
     "serves": {"household": ["single"], "min_age": 18},
     "what": "Men and women 18+. Breakfast, lunch, dinner; chairs for overnight; medical help 9am–5pm.", "source": "NCS, ODP"},
    {"id": "olivieri", "kind": "drop_in", "name": "Antonio G. Olivieri Drop-in Center",
     "address": "257 W. 30th Street (btwn 7th & 8th), Manhattan", "borough": "Manhattan", "phone": "212-947-3211",
     "hours": "Intake 4:30–5pm for an overnight chair; leave by 8:30am",
     "serves": {"household": ["single"], "min_age": 18},
     "what": "Men and women. Overnight chair, dinner at intake, showers for clients, breakfast.", "source": "NCS, ODP"},
    {"id": "living-room", "kind": "drop_in", "name": "The Living Room (BronxWorks)",
     "address": "800 Barretto Street, Bronx, NY 10474", "borough": "Bronx", "phone": "718-893-3606",
     "hours": "24 hours",
     "serves": {"household": ["single"], "min_age": 18},
     "what": "Street homeless adults: showers, laundry, hot meals, benefits and housing help, medical and psychiatric care.",
     "needs": ["mental_health", "substance_use"], "source": "BW, ODP"},
    {"id": "gathering-place", "kind": "drop_in", "name": "The Gathering Place (CAMBA)",
     "address": "2402 Atlantic Avenue, Brooklyn, NY 11233", "borough": "Brooklyn", "phone": "718-287-2600",
     "hours": "24/7, year-round",
     "serves": {"household": ["single"], "min_age": 18},
     "what": "Single men and women 18+: three meals, showers, laundry, clothing, mail, case management, medical and mental health.",
     "needs": ["mental_health"], "source": "CAMBA, ODP"},
    {"id": "project-hospitality", "kind": "drop_in", "name": "Project Hospitality Drop-in Center",
     "address": "150 Richmond Terrace, Staten Island, NY 10301", "borough": "Staten Island", "phone": "718-448-1544",
     "hours": "Call for hours",
     "serves": {"household": ["single"], "min_age": 18}, "what": "Drop-in services on Staten Island.", "source": "ODP"},
    {"id": "breaking-ground-jamaica", "kind": "drop_in", "name": "Breaking Ground Drop-in Center",
     "address": "100-32 Atlantic Avenue, Jamaica, NY 11416", "borough": "Queens", "phone": "311",
     "hours": "Call 311 for hours", "serves": {"household": ["single"], "min_age": 18},
     "what": "Drop-in services in Queens.", "source": "ODP"},
    {"id": "union-hall", "kind": "drop_in", "name": "Union Hall Drop-in Center",
     "address": "92-32 Union Hall Street, Jamaica, NY 11433", "borough": "Queens", "phone": "311",
     "hours": "Call 311 for hours", "serves": {"household": ["single"], "min_age": 18},
     "what": "Drop-in services in Queens.", "source": "ODP"},
    {"id": "paul-place", "kind": "drop_in", "name": "Paul Place Drop-in Center",
     "address": "114 W. 14th Street, New York, NY", "borough": "Manhattan", "phone": "311",
     "hours": "Call 311 for hours", "serves": {"household": ["single"], "min_age": 18},
     "what": "Drop-in services in Manhattan.", "source": "ODP"},
    {"id": "9th-street", "kind": "drop_in", "name": "9th Street Drop-In",
     "address": "771 9th Avenue, New York, NY", "borough": "Manhattan", "phone": "311",
     "hours": "Call 311 for hours", "serves": {"household": ["single"], "min_age": 18},
     "what": "Drop-in services in Manhattan.", "source": "ODP"},

    # ---------------- Safe Havens: referral only ----------------
    {"id": "safe-haven-outreach", "kind": "outreach", "name": "Safe Havens (via street outreach)",
     "address": None, "borough": None, "phone": "311 (ask for the homeless outreach team)", "hours": "Outreach 24/7",
     "serves": {"household": ["single"], "min_age": 18},
     "what": "Low-barrier beds for people living on the street who aren't ready for regular shelter. You can't apply "
             "directly: Safe Havens only take referrals from DHS street outreach teams. Call 311 and ask for outreach. "
             "BronxWorks' Westchester Avenue Safe Haven is for adults 50+.",
     "source": "BW, NCS"},

    # ---------------- Hotlines ----------------
    {"id": "dv-hotline", "kind": "hotline", "name": "NYC Domestic Violence Hotline (Safe Horizon)",
     "address": None, "borough": None, "phone": "800-621-4673 (800-621-HOPE)", "hours": "24/7",
     "serves": {"flag": "fleeing_violence"},
     "what": "Domestic violence shelters are confidential. The hotline places survivors (and their children) safely.",
     "source": "NCS"},
    {"id": "sexual-assault", "kind": "hotline", "name": "Safe Horizon Rape & Sexual Assault Hotline",
     "address": None, "borough": None, "phone": "212-227-3000", "hours": "24/7",
     "serves": {"flag": "fleeing_violence"}, "what": "Support after rape or sexual assault.", "source": "NCS"},
    {"id": "va", "kind": "hotline", "name": "Department of Veterans Affairs: homeless veterans",
     "address": None, "borough": None, "phone": "1-877-424-3838", "hours": "24/7",
     "serves": {"flag": "veteran"},
     "what": "Resources and referrals for homeless veterans. In the DHS system, veterans go through regular intake, then "
             "the Veterans Services Unit refers them to veteran housing (e.g. Borden Avenue Veterans Residence).",
     "source": "NCS, DHS"},
    {"id": "988", "kind": "hotline", "name": "988 Suicide & Crisis Lifeline", "address": None, "borough": None,
     "phone": "988", "hours": "24/7", "serves": {"need": "mental_health"},
     "what": "Crisis support, mental health and substance use information.", "source": "NCS"},
    {"id": "aa-intergroup", "kind": "hotline", "name": "AA Intergroup", "address": None, "borough": None,
     "phone": "212-647-1680", "hours": "Daily 9am–2am", "serves": {"need": "substance_use"},
     "what": "AA meetings and available detox beds.", "source": "NCS"},
    {"id": "immigration", "kind": "hotline", "name": "Catholic Charities immigration hotline", "address": None,
     "borough": None, "phone": "1-800-566-7636", "hours": "Call for hours", "serves": {"flag": "immigration_help"},
     "what": "Immigration information in multiple languages.", "source": "NCS"},
    {"id": "legal-aid", "kind": "hotline", "name": "Legal Aid Society Homeless Rights Project", "address": None,
     "borough": None, "phone": "800-649-9125", "hours": "Mon–Fri 10am–3pm", "serves": {"all": True},
     "what": "Legal help if you're denied shelter or have problems in shelter.", "source": "NCS"},
    {"id": "coalition", "kind": "hotline", "name": "Coalition for the Homeless", "address": None, "borough": None,
     "phone": "1-888-358-2384", "hours": "Leave a detailed message with a phone number", "serves": {"all": True},
     "what": "Crisis services, advocacy, and help navigating shelter.", "source": "NCS"},
    {"id": "311", "kind": "hotline", "name": "NYC 311 (shelter info + street outreach)", "address": None, "borough": None,
     "phone": "311", "hours": "24/7", "serves": {"all": True},
     "what": "Directions to intake centers; ask for the homeless outreach team to be sent to you.", "source": "NCS"},
]
