"""FastAPI backend for the Eva multi-agent marketing campaign generator."""

import asyncio
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import BackgroundTasks, FastAPI, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from src.event_bus import jobs, set_job, push
from src.graph import build_graph
from src.main import save_campaign_report
from src.state import CampaignState

app = FastAPI(title="Eva API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = Path("data")
CAMPAIGNS_DIR = Path("campaigns")

# Fields to extract for node_done events
_NODE_FIELDS = {
    "pdf_ingestion": [],
    "researcher": ["target_audience", "market_research"],
    "strateeg": ["strategy", "positioning", "tone_of_voice"],
    "copywriter": ["copy_draft"],
    "social_specialist": ["social_content"],
    "campaign_manager": ["cm_feedback", "approved", "iteration_count", "phase"],
    "image_generator": ["image_path"],
}


# --- Models ---

class CampaignRequest(BaseModel):
    product_description: str
    campaign_type: str = "product"
    pdf_path: Optional[str] = None


# --- Helpers ---

def _extract_event_data(node: str, state: dict) -> dict:
    fields = _NODE_FIELDS.get(node, [])
    return {k: state.get(k) for k in fields if state.get(k) is not None}


# --- Background task ---

def _stream_campaign(job_id: str, request: CampaignRequest):
    """Run graph.stream() in a thread. Pushes node + LLM events to jobs store."""
    set_job(job_id)  # bind job_id to this thread for event_bus
    jobs[job_id]["status"] = "running"

    try:
        graph = build_graph()
        config = {"configurable": {"thread_id": str(uuid.uuid4())}}
        initial_state: CampaignState = {
            "product_description": request.product_description,
            "campaign_type": request.campaign_type,
            "pdf_path": request.pdf_path,
            "pdf_context": "",
            "copy_versions": [],
            "social_versions": [],
            "iteration_count": 0,
            "approved": False,
        }

        final_state = {}

        for chunk in graph.stream(initial_state, config):
            for node_name, node_state in chunk.items():
                push(node_name, "node_done", f"✓ {node_name} completed",
                     _extract_event_data(node_name, node_state))
                final_state.update(node_state)

        # Save campaign report
        report_path = save_campaign_report(final_state, request.product_description)

        # Save full event log alongside the report
        events_path = report_path.replace(".json", "_events.json")
        with open(events_path, "w", encoding="utf-8") as f:
            json.dump(jobs[job_id]["events"], f, indent=2, ensure_ascii=False)

        jobs[job_id]["status"] = "done"
        jobs[job_id]["result"] = {
            "target_audience": final_state.get("target_audience", ""),
            "strategy": final_state.get("strategy", ""),
            "positioning": final_state.get("positioning", ""),
            "tone_of_voice": final_state.get("tone_of_voice", ""),
            "copy_draft": final_state.get("copy_draft", ""),
            "social_content": final_state.get("social_content", ""),
            "iterations": final_state.get("iteration_count", 0),
            "approved_by_cm": final_state.get("approved", False),
            "image_path": final_state.get("image_path"),
        }
        push("__system__", "node_done", "Campaign completed", {})

    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)
        push("__system__", "error", f"Campaign failed: {e}", {"error": str(e)})


# --- Endpoints ---

@app.post("/campaigns", status_code=202)
async def start_campaign(request: CampaignRequest, background_tasks: BackgroundTasks):
    """Start a campaign run asynchronously. Returns a job_id to poll or stream."""
    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "queued", "result": None, "error": None, "events": []}
    background_tasks.add_task(asyncio.to_thread, _stream_campaign, job_id, request)
    return {"job_id": job_id}


@app.get("/campaigns/{job_id}/stream")
async def stream_campaign_events(job_id: str):
    """SSE endpoint — streams all agent events in real-time."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    async def event_generator():
        sent = 0
        while True:
            events = jobs[job_id]["events"]
            while sent < len(events):
                yield f"data: {json.dumps(events[sent])}\n\n"
                sent += 1
            if jobs[job_id]["status"] in ("done", "failed"):
                yield f"data: {json.dumps({'node': '__done__', 'type': 'node_done', 'status': jobs[job_id]['status']})}\n\n"
                break
            await asyncio.sleep(0.2)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/campaigns/{job_id}/events")
async def get_campaign_events(job_id: str):
    """Return all events — live from memory or saved events file for older campaigns."""
    if job_id in jobs:
        return {"status": jobs[job_id]["status"], "events": jobs[job_id]["events"]}

    # Fall back to saved events file
    events_file = CAMPAIGNS_DIR / f"{job_id}_events.json"
    if events_file.exists():
        with open(events_file, encoding="utf-8") as f:
            events = json.load(f)
        return {"status": "done", "events": events}

    raise HTTPException(status_code=404, detail="Events not found")


@app.get("/campaigns/{job_id}")
async def get_campaign_status(job_id: str):
    """Poll status and final result — checks in-memory jobs first, then saved files."""
    if job_id in jobs:
        return {
            "status": jobs[job_id]["status"],
            "result": jobs[job_id]["result"],
            "error": jobs[job_id]["error"],
        }

    # Fall back to saved report file
    CAMPAIGNS_DIR.mkdir(exist_ok=True)
    report_file = CAMPAIGNS_DIR / f"{job_id}.json"
    if not report_file.exists():
        matches = sorted(CAMPAIGNS_DIR.glob(f"*{job_id}*.json"))
        # Exclude events files
        matches = [m for m in matches if "_events" not in m.name]
        if matches:
            report_file = matches[0]

    if report_file.exists():
        with open(report_file, encoding="utf-8") as f:
            data = json.load(f)
        return {"status": "done", "result": data, "error": None}

    raise HTTPException(status_code=404, detail="Campaign not found")


@app.get("/campaigns")
async def list_campaigns():
    """List all saved campaign reports (excludes events files)."""
    CAMPAIGNS_DIR.mkdir(exist_ok=True)
    reports = []
    for f in sorted(CAMPAIGNS_DIR.glob("*.json"), reverse=True):
        if "_events" in f.name:
            continue
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


# Serve campaign images (campaigns/images/) at /static/images/
CAMPAIGNS_DIR.mkdir(exist_ok=True)
(CAMPAIGNS_DIR / "images").mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(CAMPAIGNS_DIR)), name="static")
