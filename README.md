# Voucher Discrimination Detector

Finds illegal source-of-income discrimination against NYC CityFHEPS voucher holders in rental listings, shows the clause and the math, and produces an evidence packet a tenant or caseworker can use. Nothing is ever filed automatically, and no landlord is ever contacted.

## Quick start

```bash
bun install
bun test                        # core tests (offline)
bun run demo                    # terminal walkthrough + writes data/cache/demo-packet.html
bun run eval                    # dev set
bun run eval -- --holdout       # held-out set
cp .env.example .env            # add GEMINI_API_KEY to turn on Gemini extraction + translation
bun run eval -- --holdout --gemini
```

## Layout

| dir | what | status |
|---|---|---|
| `/core` | extraction (Gemini + offline regex fallback), rules R1–R4, evidence packet | **done** |
| `/config` | CityFHEPS numbers, legal text, phrase lists, thresholds | done; **verify numbers** |
| `/eval` | precision / recall / confusion matrix, per rule | done |
| `/data/labeled` | 84 labeled listings (dev 59, holdout 25) | needs human verification + ~65 real listings |
| `/scanner` | `fetchListing` / `analyzeUrl` (jev browser agent → HTTP fallback) | fetch done; batch + Mongo TODO |
| `/agent` | Photon Spectrum iMessage agent | teammate |
| `/web` | Next.js dashboard | teammate |
| `/legacy` | original Python prototype (Claude-based) | reference only |

## Using `/core`

```ts
import { analyze, buildPacket } from "@vdd/core";

const result = await analyze({ text, image: { base64, mimeType: "image/jpeg" }, hints: { bedrooms: 2 } });
result.verdict;          // "violation" | "needs_review" | "no_issue_found"
result.flags;            // [{ rule_id, code, severity, evidence_text, span, explanation, calculation? }]
const packet = await buildPacket(result, { tenantLanguage: "es", packetUrl });
packet.summaryText;      // send as the iMessage reply
packet.html;             // serve at packetUrl
```

`analyze` never throws on a Gemini failure. If the call times out or the output fails zod validation, it falls back to the offline extractor and adds a note. An unreadable image returns `needs_review` with a "try again or paste the text" note.

For URLs, `analyzeUrl(url)` in `scanner/src/analyzeUrl.ts` does fetch → analyze in one call.

## How a verdict is made

Gemini extracts facts only (rent, bedrooms, income requirement, exclusion phrases, language, translation). The **rules engine decides**, with no LLM involved:

- **R1 Explicit exclusion**: phrase list (EN/ES/ZH/RU/BN + misspellings + coded phrases like "no third-party payments") run over the listing, the text read from the image, and the English translation. An exclusion Gemini found that the phrase list missed only counts if its quote is really in the text, and then only as `review`.
- **R2 Income applied to full rent**: builds the arithmetic step by step: requirement × rent, the tenant's 30% share for an illustrative household, the lawful requirement on that share, and the full-rent requirement. Lawful cases: tenant-share carve-outs, "vouchers welcome", government lottery/AMI bands. Unknown rent, or rent above the payment standard, gives `review`.
- **R3 Other barriers**: employment-only and credit minimums give `review` (config switch if guidance clearly supports `violation`).
- **R4 Voucher range**: is the rent within the CityFHEPS payment standard for the bedroom count? Informational; feeds the split-screen view.

## jev-ultrafast (browser agent)

[browser-use/jev-ultrafast](https://github.com/browser-use/jev-ultrafast) opens a listing URL in Chrome, dismisses pop-ups, clicks "See more", and hands back the full page text plus a screenshot. It handles JavaScript-heavy pages that a plain fetch misses.

- `scanner/jev/fetch_listing.py` runs jev's predict/act loop itself and **refuses** any action that could reach a landlord: typing into any field, or clicking anything labeled contact / message / apply / call / schedule / sign in. This guard is code, not a prompt.
- Setup: `brew install uv`, clone jev, fill its `.env` (`TYPESAFE_API_KEY`, `TEXT_MODEL_API_KEY`), set `JEV_DIR` in ours. Without it, `fetchListing` falls back to a plain HTTP fetch.

## Eval: read before quoting numbers

Current offline results (regex extractor, no Gemini):

| set | n | violation precision | violation recall | false alarms |
|---|---|---|---|---|
| dev | 59 | 100% | 100% | 0% |
| holdout | 25 | 100% | 91% | 0% |

- **The holdout is contaminated.** Some phrase patterns were added after its misses were seen in the Python prototype (which scored 90% precision / 69% recall on it, the last clean number). Before the pitch, have someone who hasn't read `config/phrases.ts` write `data/labeled/holdout_v2.jsonl`, and quote that.
- All labels have `verified_by: null`. The spec requires a person to check every label.
- The spec asks for ~150 listings. Add real cached listings to `data/labeled/real.jsonl` and run `bun run eval -- --file data/labeled/real.jsonl`.
