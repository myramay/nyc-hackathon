"""HTTP API so the TypeScript pieces (Photon iMessage agent, Next.js dashboard)
can use the Python engine.

    uvicorn core.api:app --reload --port 8000      docs at http://localhost:8000/docs
                                                   camera scanner at http://localhost:8000/camera-scan/
"""
from __future__ import annotations

from pathlib import Path

from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from core import analyze, approve_draft, build_packet, draft_complaint, gemini_available, GEMINI_MODEL
from core.complaint import ComplaintDraft, Contact, ListingInfo, Reporter, Respondent
from core.schema import AnalysisResult, ListingInput

app = FastAPI(title="Voucher Discrimination Detector")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


# The camera scanner page (browser JS for the webcam; checking + drafting go through this API).
app.mount("/camera-scan", StaticFiles(directory=Path(__file__).resolve().parent.parent / "camera-scan", html=True), name="camera-scan")


from shelters.match import MatchResult, Profile, directory, match as match_shelters  # noqa: E402

app.mount("/shelter-finder", StaticFiles(directory=Path(__file__).resolve().parent.parent / "shelter-finder", html=True), name="shelter-finder")


@app.post("/shelters/match", response_model=MatchResult)
def shelters_match(profile: Profile):
    """Narrow down shelter options from a person's situation. Nothing is stored."""
    return match_shelters(profile)


@app.get("/shelters/directory")
def shelters_directory():
    """Official NYC shelter directory (NYC Open Data): shelters, drop-in centers, Homebase offices."""
    return directory()


@app.get("/camera", include_in_schema=False)
def camera():
    return RedirectResponse("/camera-scan/")


@app.get("/health")
def health():
    return {"ok": True, "gemini": gemini_available(), "model": GEMINI_MODEL}


class AnalyzeRequest(ListingInput):
    use_gemini: bool = True


@app.post("/analyze", response_model=AnalysisResult)
def analyze_listing(req: AnalyzeRequest):
    return analyze(req, use_gemini=req.use_gemini)


class AnalyzeUrlRequest(BaseModel):
    url: str
    bedrooms: Optional[float] = None
    monthly_rent: Optional[float] = None


@app.post("/analyze-url")
def analyze_listing_url(req: AnalyzeUrlRequest):
    from scanner.analyze_url import analyze_url
    result, fetched = analyze_url(req.url, {"bedrooms": req.bedrooms, "monthly_rent": req.monthly_rent})
    return {"result": result, "fetched": {k: v for k, v in fetched.items() if k != "screenshot_b64"}}


class PacketRequest(BaseModel):
    result: AnalysisResult
    tenant_language: Optional[str] = None
    packet_url: Optional[str] = None
    listing_url: Optional[str] = None


@app.post("/packet")
def packet(req: PacketRequest):
    return build_packet(req.result, req.tenant_language, req.packet_url, req.listing_url)


class ComplaintRequest(BaseModel):
    result: AnalysisResult
    agency: str = "cchr"
    listing: Optional[ListingInfo] = None
    respondent: Optional[Respondent] = None
    reporter: Optional[Reporter] = None
    contact: Optional[Contact] = None
    tenant_language: Optional[str] = None


@app.post("/complaint", response_model=ComplaintDraft)
def complaint(req: ComplaintRequest):
    try:
        return draft_complaint(req.result, req.agency, req.listing, req.respondent, req.reporter, req.contact, req.tenant_language)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


class ApproveRequest(BaseModel):
    draft: ComplaintDraft
    reviewer: str


@app.post("/complaint/approve", response_model=ComplaintDraft)
def complaint_approve(req: ApproveRequest):
    """Records a human review. Sends nothing."""
    try:
        return approve_draft(req.draft, req.reviewer)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.post("/complaint/html", response_class=HTMLResponse)
def complaint_html(draft: ComplaintDraft):
    return draft.html
