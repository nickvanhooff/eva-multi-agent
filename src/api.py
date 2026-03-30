"""FastAPI backend for the Eva multi-agent marketing campaign generator."""

import asyncio
import json
import uuid
from pathlib import Path
from typing import Optional

from fastapi import BackgroundTasks, FastAPI, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.main import run_campaign, save_campaign_report

app = FastAPI(title="Eva API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory job store: {job_id: {status, result, error}}
jobs: dict[str, dict] = {}

DATA_DIR = Path("data")
CAMPAIGNS_DIR = Path("campaigns")


# --- Models ---

class CampaignRequest(BaseModel):
    product_description: str
    campaign_type: str = "product"
    pdf_path: Optional[str] = None


# --- Background task ---

async def _run_campaign_task(job_id: str, request: CampaignRequest):
    jobs[job_id]["status"] = "running"
    try:
        result = await asyncio.to_thread(
            run_campaign,
            request.product_description,
            request.pdf_path,
            request.campaign_type,
        )
        save_campaign_report(result, request.product_description)
        jobs[job_id]["status"] = "done"
        jobs[job_id]["result"] = {
            "target_audience": result.get("target_audience", ""),
            "strategy": result.get("strategy", ""),
            "positioning": result.get("positioning", ""),
            "tone_of_voice": result.get("tone_of_voice", ""),
            "copy_draft": result.get("copy_draft", ""),
            "social_content": result.get("social_content", ""),
            "iterations": result.get("iteration_count", 0),
            "approved_by_cm": result.get("approved", False),
            "image_path": result.get("image_path"),
        }
    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)


# --- Endpoints ---

@app.post("/campaigns", status_code=202)
async def start_campaign(request: CampaignRequest, background_tasks: BackgroundTasks):
    """Start a campaign run asynchronously. Returns a job_id to poll."""
    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "queued", "result": None, "error": None}
    background_tasks.add_task(_run_campaign_task, job_id, request)
    return {"job_id": job_id}


@app.get("/campaigns/{job_id}")
async def get_campaign_status(job_id: str):
    """Poll status of a running or completed campaign job."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs[job_id]


@app.get("/campaigns")
async def list_campaigns():
    """List all saved campaign reports from the campaigns/ directory."""
    CAMPAIGNS_DIR.mkdir(exist_ok=True)
    reports = []
    for f in sorted(CAMPAIGNS_DIR.glob("*.json"), reverse=True):
        try:
            with open(f, encoding="utf-8") as fh:
                data = json.load(fh)
                data["filename"] = f.name
                reports.append(data)
        except Exception:
            pass
    return reports


@app.get("/pdfs")
async def list_pdfs():
    """List available PDFs in the data/ directory."""
    DATA_DIR.mkdir(exist_ok=True)
    return [f.name for f in sorted(DATA_DIR.glob("*.pdf"))]


@app.post("/pdfs/upload")
async def upload_pdf(file: UploadFile):
    """Upload a PDF to the data/ directory."""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    DATA_DIR.mkdir(exist_ok=True)
    dest = DATA_DIR / file.filename
    content = await file.read()
    dest.write_bytes(content)
    return {"filename": file.filename, "path": str(dest)}
