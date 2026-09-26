# Voucher Discrimination Detector

Finds illegal source-of-income discrimination against NYC CityFHEPS voucher holders in rental listings, shows the clause and the math, and produces an evidence packet and a human-reviewed complaint draft. Nothing is filed automatically, and no landlord is ever contacted.

## Quick start (Python 3.9+)

```bash
pip install -r requirements.txt
cp .env.example .env                        # add GEMINI_API_KEY (optional; works offline without it)

python -m unittest discover tests            # 23 tests, offline
python demo.py                               # walkthrough + data/cache/demo-packet.html + demo-complaint.html
python -m eval.run --v2                      # blind test set: the number for the pitch
uvicorn core.api:app --reload --port 8000    # HTTP API for the iMessage agent + dashboard; docs at /docs
python -m eval.review --by "Your Name"       # label review page: http://localhost:4321
```

`.env` is read automatically and is in `.gitignore`.

## Layout

| dir | what | language |
|---|---|---|
| `core/` | engine: extraction (Gemini + offline fallback), rules R1–R4, evidence packet, complaint drafts, FastAPI server | Python |
| `config/` | CityFHEPS numbers, legal text, agencies, phrase lists, thresholds (**verify numbers**) | Python |
| `scanner/` | `analyze_url()`: listing link → jev browser agent (or plain download) → engine | Python |
| `eval/` | precision/recall script, label review page | Python |
| `data/labeled/` | 144 labeled listings, rubric, blind agent labels | JSONL |
| `tests/` | unit tests | Python |
| `/agent` | Photon Spectrum iMessage bot: **must be TypeScript** (Spectrum is TS-only); calls the API | teammate |
| `/web` | Next.js dashboard; calls the API | teammate |
| `legacy/` | earlier versions (TypeScript port, first Python prototype), reference only | |

## Using it from Python

```python
from core import analyze, build_packet, draft_complaint, approve_draft

result = analyze({"text": text, "image": {"base64": b64, "mime_type": "image/jpeg"}, "hints": {"bedrooms": 2}})
result.verdict      # "violation" | "needs_review" | "no_issue_found"
result.flags        # [Flag(rule_id, code, severity, evidence_text, span, explanation, calculation)]

packet = build_packet(result, tenant_language="es", packet_url=url)
packet.summary_text # iMessage reply
packet.html         # shareable page

draft = draft_complaint(result, agency="cchr", listing={"source": "Craigslist", "url": url, "screenshot_saved": True},
                        reporter={"role": "caseworker"}, tenant_language="es")
draft.form          # answers for the CCHR online form, field by field
draft.blocking      # must be fixed before submitting (missing respondent name, screenshot, ...)
draft.html          # printable review page with Copy buttons
approve_draft(draft, "Reviewer name")   # records the review; still sends nothing
```

`analyze` never raises on a Gemini failure. A 503 ("high demand") is retried; anything else, including a 429 quota error, falls back to the offline extractor with a short note. Set `VDD_DEBUG=1` to see the full Gemini errors.

## Using it from TypeScript (iMessage agent, dashboard)

Run `uvicorn core.api:app --port 8000`, then:

| endpoint | body | returns |
|---|---|---|
| `POST /analyze` | `{text?, image?: {base64, mime_type}, hints?, use_gemini?}` | analysis result |
| `POST /analyze-url` | `{url, bedrooms?, monthly_rent?}` | `{result, fetched}` |
| `POST /packet` | `{result, tenant_language?, packet_url?, listing_url?}` | `{summary_text, html, ...}` |
| `POST /complaint` | `{result, agency?, listing?, respondent?, reporter?, contact?, tenant_language?}` | draft (422 if no issue found) |
| `POST /complaint/approve` | `{draft, reviewer}` | draft marked reviewed (sends nothing) |
| `POST /complaint/html` | a draft | the review page as HTML |
| `GET /health` | | `{ok, gemini, model}` |

Full schemas at http://localhost:8000/docs.

## How a verdict is made

Gemini extracts facts only (rent, bedrooms, income requirement, exclusion phrases, contact, language, translation). The **rules engine decides**, with no model involved:

- **R1 Explicit exclusion**: phrase list (EN/ES/ZH/RU/BN + misspellings + coded phrases like "no third-party payments") run over the listing, the text read from the image, and the English translation. An exclusion Gemini found that the phrase list missed only counts if its quote is really in the text, and then only as `review`.
- **R2 Income applied to full rent**: builds the math step by step (requirement × rent, the tenant's 30% share for an illustrative household, the lawful requirement on that share, the full-rent requirement). Lawful: tenant-share carve-outs, "vouchers welcome", lottery/AMI bands. Unknown rent or rent above the payment standard gives `review`.
- **R3 Other barriers**: employment-only and credit minimums give `review` (switch in `config/thresholds.py`).
- **R4 Voucher range**: is the rent within the CityFHEPS payment standard? Informational; feeds the split-screen view.

## Complaint drafts (human-reviewed, never auto-filed)

- **Matches the real CCHR form** (nyc.gov/site/cchr/about/report-discrimination.page), field by field. Each answer is `auto` (from the listing), `suggested` (confirm it), or `you` (only the person can answer).
- **Never pre-filled:** the person's name and contact info, "filed with us before?", and the required acknowledgment checkbox.
- **The narrative is a template**, not model-written: it only states facts from the flagged clauses and the math, quotes full sentences, and says the listing was found with an automated tool and checked by a person.
- **Deadlines:** CCHR one year from the last act; NYS Division of Human Rights (`agency="nysdhr"`) three years for incidents on or after Feb 15, 2024. CCHR can't take a complaint already filed elsewhere, so the draft makes the reviewer answer that.

## jev-ultrafast (browser agent) on OpenJev

[browser-use/jev-ultrafast](https://github.com/browser-use/jev-ultrafast) opens a listing link, dismisses pop-ups, clicks "See more", and returns the full page text plus a screenshot. `scanner/jev/fetch_listing.py` runs jev's steps itself and **blocks** typing into any field and clicking anything labeled contact / message / apply / call / schedule / sign in, so it can't contact a landlord.

jev's decisions come from a "System One" model API. TypeSafe's hosted API is paused, so we use **[OpenJev](https://github.com/razorback16/openjev)**, an open-source server with the same API (open model: DiffusionGemma 26B-A4B), hosted free at Codiv. jev hardcodes TypeSafe's URL, so the sidecar redirects it when `TYPESAFE_BASE_URL` is set.

Setup:
```bash
brew install uv
git clone https://github.com/browser-use/jev-ultrafast.git ~/jev-ultrafast
cd ~/jev-ultrafast && uv sync
```
Then in our `.env`:
```
JEV_DIR=/Users/<you>/jev-ultrafast
TYPESAFE_BASE_URL=https://api.codiv.ai     # or http://127.0.0.1:8080 for a self-hosted OpenJev
TYPESAFE_API_KEY=sk-codiv-...              # free Codiv key (codiv.ai)
TYPESAFE_MODEL=openjev-latest
```
`TEXT_MODEL_API_KEY` is only used to type into fields, which our guard blocks, so it shouldn't be needed. Without any of this, links fall back to a plain download. Listing page text is sent to Codiv to choose clicks; it's public listing content, never tenant data.

## Eval: read before quoting numbers

Offline results (regex extractor, no Gemini):

| set | n | violation precision | violation recall | reaches a human | false alarms |
|---|---|---|---|---|---|
| dev (rules built from it) | 59 | 100% | 100% | 100% | 0% |
| holdout v1 (contaminated) | 25 | 100% | 91% | 91% | 0% |
| **holdout_v2 (blind; quote this)** | **60** | **92.9%** | **59.1%** | **63.6%** | **3.8%** |

- `holdout_v2` was written by an agent that only saw `data/labeled/RUBRIC.md`, never the rules. **Don't change rules because of its misses**; if you do, the number stops being honest and you need a v3.
- Misses are mostly paraphrases and non-English refusals the phrase list doesn't know. That's Gemini's job; rerun with `--gemini` once the key has quota.
- Two blind agents pre-labeled the data (`data/labeled/agent/`). A person verifies each label with `python -m eval.review --by "Name"` (1/2/3 pick, Enter accepts, Backspace goes back).
- The rubric was written knowing the existing labels, so agent agreement partly reflects the rubric.
- Total labeled: 144. For ~150, add real cached listings to `data/labeled/real.jsonl` and run `python -m eval.run --file data/labeled/real.jsonl`.
