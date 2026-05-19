"""FastAPI backend for the Eva multi-agent marketing campaign generator."""

import asyncio
import json
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import BackgroundTasks, FastAPI, HTTPException, UploadFile
from langgraph.types import Command
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from src.agents.website_generator import generate_website
from src.event_bus import jobs, set_job, push
from src.graph import build_graph
from src.main import save_campaign_report
from src.state import CampaignState
from src.runtime_config import apply_config, get_public_config, reset_to_defaults
from src.tracing import setup_tracing

app = FastAPI(title="Eva API", version="1.0.0")

# Initialize LangSmith tracing on startup (requires LANGSMITH_ENABLED=true + LANGSMITH_API_KEY in .env)
setup_tracing()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = Path("data")
CAMPAIGNS_DIR = Path("campaigns")
WEBSITES_DIR = CAMPAIGNS_DIR / "websites"


_CAMPAIGN_STEM_RE = re.compile(r"^campaign_(\d{8})_(\d{6})$")
# Max gap between campaign JSON time and website HTML time for legacy orphan linking
WEBSITE_ORPHAN_MATCH_SEC = 3600

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


class ResumeRequest(BaseModel):
    answer: str


class AgentLLMConfig(BaseModel):
    provider: str
    model: str
    temperature: float = 0.7


class ConfigUpdate(BaseModel):
    max_iterations: Optional[int] = None
    agents: Optional[dict[str, AgentLLMConfig]] = None


# --- Helpers ---

def _extract_event_data(node: str, state: dict) -> dict:
    fields = _NODE_FIELDS.get(node, [])
    return {k: state.get(k) for k in fields if state.get(k) is not None}


def _find_report_file(job_id: str) -> Path | None:
    """Locate the campaign JSON report for a UUID, filename stem, or partial id."""
    if job_id in jobs and jobs[job_id].get("report_file"):
        path = Path(jobs[job_id]["report_file"])
        if path.exists():
            return path

    candidate = CAMPAIGNS_DIR / f"{job_id}.json"
    if candidate.exists():
        return candidate

    matches = sorted(CAMPAIGNS_DIR.glob(f"*{job_id}*.json"))
    matches = [m for m in matches if "_events" not in m.name]
    return matches[0] if matches else None


def _parse_campaign_stem_ts(stem: str) -> datetime | None:
    match = _CAMPAIGN_STEM_RE.match(stem)
    if not match:
        return None
    try:
        return datetime.strptime(match.group(1) + match.group(2), "%Y%m%d%H%M%S")
    except ValueError:
        return None


def _html_to_static_url(html_file: Path) -> str:
    rel = html_file.as_posix().replace("campaigns/", "", 1)
    return f"/static/{rel}"


def _website_stem_from_url(html_url: str) -> str | None:
    """Extract campaign stem from /static/websites/campaign_YYYYMMDD_HHMMSS.html."""
    if not html_url:
        return None
    name = html_url.rstrip("/").split("/")[-1]
    if not name.endswith(".html"):
        return None
    stem = name[: -len(".html")]
    return stem if _CAMPAIGN_STEM_RE.match(stem) else None


def _campaign_day_prefix(stem: str) -> str | None:
    match = _CAMPAIGN_STEM_RE.match(stem)
    return f"campaign_{match.group(1)}" if match else None


def _same_campaign_day(stem_a: str, stem_b: str) -> bool:
    day_a = _campaign_day_prefix(stem_a)
    day_b = _campaign_day_prefix(stem_b)
    return bool(day_a and day_b and day_a == day_b)


def _website_belongs_to_campaign(html_url: str, campaign_stem: str) -> bool:
    """HTML filename stem matches the campaign report stem."""
    return _website_stem_from_url(html_url) == campaign_stem


def _url_to_html_file(html_url: str) -> Path | None:
    stem = _website_stem_from_url(html_url)
    if not stem:
        return None
    path = WEBSITES_DIR / f"{stem}.html"
    return path if path.is_file() else None


def _campaign_image_basename(result: dict) -> str | None:
    image_path = result.get("image_path") or ""
    if not image_path:
        return None
    return Path(image_path.replace("\\", "/")).name


def _html_references_image(html_file: Path, image_basename: str) -> bool:
    if not image_basename or not html_file.is_file():
        return False
    try:
        return image_basename in html_file.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return False


def _pick_best_html_match(campaign_stem: str, matches: list[Path]) -> Path:
    exact = WEBSITES_DIR / f"{campaign_stem}.html"
    if exact in matches:
        return exact
    target_ts = _parse_campaign_stem_ts(campaign_stem)
    if target_ts and len(matches) > 1:
        def delta(path: Path) -> float:
            html_ts = _parse_campaign_stem_ts(path.stem)
            return abs((html_ts - target_ts).total_seconds()) if html_ts else float("inf")

        return min(matches, key=delta)
    return matches[0]


def _discover_website_by_image(campaign_stem: str, result: dict) -> str | None:
    """Match legacy HTML files that embed this campaign's hero image."""
    image_name = _campaign_image_basename(result)
    if not image_name or not WEBSITES_DIR.exists():
        return None
    matches = [
        path
        for path in WEBSITES_DIR.glob("campaign_*.html")
        if _same_campaign_day(campaign_stem, path.stem)
        and _html_references_image(path, image_name)
    ]
    if not matches:
        return None
    return _html_to_static_url(_pick_best_html_match(campaign_stem, matches))


def _website_matches_campaign(html_url: str, campaign_stem: str, result: dict) -> bool:
    """Exact filename match, or HTML references this campaign's image."""
    if _website_belongs_to_campaign(html_url, campaign_stem):
        return True
    html_file = _url_to_html_file(html_url)
    image_name = _campaign_image_basename(result)
    return bool(html_file and image_name and _html_references_image(html_file, image_name))


def _discover_website_url(campaign_stem: str, result: dict) -> str | None:
    """Exact stem file, else HTML that references the campaign image."""
    if not campaign_stem or not WEBSITES_DIR.exists():
        return None

    exact = WEBSITES_DIR / f"{campaign_stem}.html"
    if exact.exists():
        return _html_to_static_url(exact)
    return _discover_website_by_image(campaign_stem, result)


def _compute_website_map(campaigns: list[tuple[str, dict]]) -> dict[str, str]:
    """Assign each website HTML to at most one campaign (exact → image → timestamp)."""
    if not WEBSITES_DIR.exists():
        return {}

    mapping: dict[str, str] = {}
    used_html: set[str] = set()

    for stem, data in campaigns:
        exact = WEBSITES_DIR / f"{stem}.html"
        if exact.is_file():
            mapping[stem] = _html_to_static_url(exact)
            used_html.add(stem)

    for stem, data in campaigns:
        if stem in mapping:
            continue
        url = _discover_website_by_image(stem, data)
        if not url:
            continue
        html_stem = _website_stem_from_url(url)
        if html_stem and html_stem not in used_html:
            mapping[stem] = url
            used_html.add(html_stem)

    pairs: list[tuple[float, str, Path]] = []
    for stem, _data in campaigns:
        if stem in mapping:
            continue
        target_ts = _parse_campaign_stem_ts(stem)
        if not target_ts:
            continue
        for html_file in WEBSITES_DIR.glob("campaign_*.html"):
            if html_file.stem in used_html:
                continue
            if not _same_campaign_day(stem, html_file.stem):
                continue
            html_ts = _parse_campaign_stem_ts(html_file.stem)
            if not html_ts:
                continue
            delta = abs((html_ts - target_ts).total_seconds())
            if delta <= WEBSITE_ORPHAN_MATCH_SEC:
                pairs.append((delta, stem, html_file))

    pairs.sort(key=lambda item: item[0])
    for _delta, stem, html_file in pairs:
        if stem in mapping or html_file.stem in used_html:
            continue
        mapping[stem] = _html_to_static_url(html_file)
        used_html.add(html_file.stem)

    return mapping


def _load_campaign_reports() -> list[tuple[str, dict, Path]]:
    CAMPAIGNS_DIR.mkdir(exist_ok=True)
    loaded: list[tuple[str, dict, Path]] = []
    for report_file in sorted(CAMPAIGNS_DIR.glob("*.json"), reverse=True):
        if "_events" in report_file.name:
            continue
        try:
            with open(report_file, encoding="utf-8") as fh:
                data = json.load(fh)
            data["filename"] = report_file.name
            loaded.append((report_file.stem, data, report_file))
        except Exception:
            pass
    return loaded


def _attach_website_to_result(
    result: dict | None,
    job_id: str,
    report_file: Path | None = None,
    persist: bool = False,
    website_map: dict[str, str] | None = None,
) -> dict | None:
    """Ensure result has html_path when a website file exists on disk."""
    if not result:
        return result

    report_file = report_file or _find_report_file(job_id)
    campaign_stem = report_file.stem if report_file else (
        job_id if job_id.startswith("campaign_") else None
    )

    html_url = result.get("html_path")
    if html_url and not html_url.startswith("/static/"):
        html_url = f"/static/{html_url.lstrip('/')}"

    if html_url and campaign_stem and not _website_matches_campaign(
        html_url, campaign_stem, result
    ):
        html_url = None

    if not html_url and campaign_stem and website_map:
        html_url = website_map.get(campaign_stem)

    if not html_url and campaign_stem:
        sidecar = CAMPAIGNS_DIR / f"{campaign_stem}.website"
        if sidecar.exists():
            candidate = sidecar.read_text(encoding="utf-8").strip()
            if candidate and _website_matches_campaign(candidate, campaign_stem, result):
                html_url = candidate

    if not html_url and campaign_stem:
        html_url = _discover_website_url(campaign_stem, result)

    if html_url:
        result["html_path"] = html_url
    elif "html_path" in result:
        del result["html_path"]

    if persist and report_file and report_file.exists():
        try:
            with open(report_file, encoding="utf-8") as f:
                saved = json.load(f)
            changed = False
            if html_url:
                if saved.get("html_path") != html_url:
                    saved["html_path"] = html_url
                    changed = True
            elif saved.pop("html_path", None) is not None:
                changed = True
            if changed:
                with open(report_file, "w", encoding="utf-8") as f:
                    json.dump(saved, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    return result


# --- Background task ---

def _finish_campaign(job_id: str, final_state: dict, product_description: str):
    """Save campaign report and mark job as done."""
    report_path = save_campaign_report(final_state, product_description)

    events_path = report_path.replace(".json", "_events.json")
    with open(events_path, "w", encoding="utf-8") as f:
        json.dump(jobs[job_id]["events"], f, indent=2, ensure_ascii=False)

    jobs[job_id]["status"] = "done"
    jobs[job_id]["report_file"] = report_path
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
        "pdf_sources": final_state.get("pdf_sources", []),
        "product_description": product_description,
        "campaign_type": final_state.get("campaign_type", "product"),
    }
    push("__system__", "node_done", "Campaign completed", {})


def _run_stream(job_id: str, stream_iter) -> tuple[dict, bool]:
    """Consume a graph stream iterator. Returns (final_state, interrupted)."""
    final_state = {}
    for chunk in stream_iter:
        if "__interrupt__" in chunk:
            interrupt_data = chunk["__interrupt__"][0].value
            jobs[job_id]["status"] = "awaiting_input"
            push("__system__", "awaiting_input", interrupt_data["question"], interrupt_data)
            return final_state, True
        for node_name, node_state in chunk.items():
            push(node_name, "node_done", f"✓ {node_name} completed",
                 _extract_event_data(node_name, node_state))
            final_state.update(node_state)
    return final_state, False


def _stream_campaign(job_id: str, request: CampaignRequest):
    """Run graph.stream() in a thread. Pushes node + LLM events to jobs store."""
    set_job(job_id)
    jobs[job_id]["status"] = "running"

    try:
        graph = build_graph()
        config = {"configurable": {"thread_id": str(uuid.uuid4())}}

        # Store graph + config so the job can be resumed after an interrupt
        jobs[job_id]["graph"] = graph
        jobs[job_id]["config"] = config
        jobs[job_id]["product_description"] = request.product_description

        initial_state: CampaignState = {
            "product_description": request.product_description,
            "campaign_type": request.campaign_type,
            "pdf_path": request.pdf_path,
            "pdf_context": "",
            "pdf_sources": [],
            "copy_versions": [],
            "social_versions": [],
            "iteration_count": 0,
            "approved": False,
        }

        final_state, interrupted = _run_stream(job_id, graph.stream(initial_state, config))
        if not interrupted:
            _finish_campaign(job_id, final_state, request.product_description)

    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)
        push("__system__", "error", f"Campaign failed: {e}", {"error": str(e)})


def _stream_campaign_resume(job_id: str, answer: str):
    """Resume a graph that was paused by interrupt(). Runs in a background thread."""
    set_job(job_id)
    jobs[job_id]["status"] = "running"

    try:
        graph = jobs[job_id]["graph"]
        config = jobs[job_id]["config"]
        product_description = jobs[job_id].get("product_description", "")

        final_state, interrupted = _run_stream(job_id, graph.stream(Command(resume=answer), config))
        if not interrupted:
            # Use full checkpointed state — stream chunks after resume don't include
            # outputs from nodes that ran before the interrupt (e.g. pdf_sources)
            complete_state = dict(graph.get_state(config).values)
            _finish_campaign(job_id, complete_state, product_description)

    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)
        push("__system__", "error", f"Campaign failed after resume: {e}", {"error": str(e)})


# --- Endpoints ---

@app.get("/config")
async def get_config():
    """Runtime LLM settings per agent (no API keys)."""
    return get_public_config()


@app.put("/config")
async def update_config(body: ConfigUpdate):
    """Update runtime LLM settings; persisted to data/runtime_config.json."""
    payload = body.model_dump(exclude_none=True)
    try:
        return apply_config(payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.post("/config/reset")
async def reset_config():
    """Restore default agent models and max_iterations."""
    return reset_to_defaults()


@app.post("/campaigns", status_code=202)
async def start_campaign(request: CampaignRequest, background_tasks: BackgroundTasks):
    """Start a campaign run asynchronously. Returns a job_id to poll or stream."""
    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "queued", "result": None, "error": None, "events": []}
    background_tasks.add_task(asyncio.to_thread, _stream_campaign, job_id, request)
    return {"job_id": job_id}


@app.post("/campaigns/{job_id}/resume", status_code=200)
async def resume_campaign(job_id: str, body: ResumeRequest, background_tasks: BackgroundTasks):
    """Resume a campaign that was paused by a human-in-the-loop interrupt."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    if jobs[job_id]["status"] != "awaiting_input":
        raise HTTPException(status_code=400, detail="Job is not waiting for input")
    background_tasks.add_task(asyncio.to_thread, _stream_campaign_resume, job_id, body.answer)
    return {"status": "resumed"}


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
    report_file = _find_report_file(job_id)
    loaded = _load_campaign_reports()
    website_map = _compute_website_map([(stem, data) for stem, data, _ in loaded])

    if job_id in jobs:
        result = _attach_website_to_result(
            jobs[job_id]["result"],
            job_id,
            report_file,
            persist=True,
            website_map=website_map,
        )
        return {
            "status": jobs[job_id]["status"],
            "result": result,
            "error": jobs[job_id]["error"],
        }

    if report_file and report_file.exists():
        with open(report_file, encoding="utf-8") as f:
            data = json.load(f)
        data = _attach_website_to_result(
            data, job_id, report_file, persist=True, website_map=website_map
        )
        return {"status": "done", "result": data, "error": None}

    raise HTTPException(status_code=404, detail="Campaign not found")


@app.get("/campaigns")
async def list_campaigns():
    """List all saved campaign reports (excludes events files)."""
    loaded = _load_campaign_reports()
    website_map = _compute_website_map([(stem, data) for stem, data, _ in loaded])
    reports = []
    for stem, data, report_file in loaded:
        data = _attach_website_to_result(
            data, stem, report_file, persist=False, website_map=website_map
        ) or data
        reports.append(data)
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


@app.post("/campaigns/{job_id}/generate-website")
async def generate_website_endpoint(job_id: str):
    """Generate a Tailwind HTML landing page from an existing campaign result."""
    report_file = _find_report_file(job_id)
    campaign_data = None

    if job_id in jobs and jobs[job_id].get("result"):
        campaign_data = dict(jobs[job_id]["result"])

    if report_file and report_file.exists():
        with open(report_file, encoding="utf-8") as f:
            from_disk = json.load(f)
        campaign_data = {**from_disk, **(campaign_data or {})}

    if not campaign_data:
        raise HTTPException(status_code=404, detail="Campaign result not found")

    if not report_file:
        raise HTTPException(
            status_code=400,
            detail="Campaign report not found on disk; run the campaign first.",
        )

    output_stem = report_file.stem
    result = await asyncio.to_thread(
        generate_website, campaign_data, output_stem=output_stem
    )

    raw_path = Path(result["html_path"].replace("\\", "/"))
    canonical = WEBSITES_DIR / f"{output_stem}.html"
    if raw_path.resolve() != canonical.resolve() and raw_path.is_file():
        canonical.parent.mkdir(parents=True, exist_ok=True)
        if canonical.is_file():
            canonical.unlink()
        raw_path.rename(canonical)
        raw_path = canonical

    html_url = _html_to_static_url(raw_path)

    if job_id in jobs and jobs[job_id].get("result") is not None:
        jobs[job_id]["result"]["html_path"] = html_url

    if report_file and report_file.exists():
        with open(report_file, encoding="utf-8") as f:
            saved = json.load(f)
        saved["html_path"] = html_url
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(saved, f, indent=2, ensure_ascii=False)
        sidecar = CAMPAIGNS_DIR / f"{report_file.stem}.website"
        sidecar.write_text(html_url, encoding="utf-8")

    return {"html_path": html_url}


# Serve campaign output files at /static/
CAMPAIGNS_DIR.mkdir(exist_ok=True)
(CAMPAIGNS_DIR / "images").mkdir(exist_ok=True)
(CAMPAIGNS_DIR / "websites").mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(CAMPAIGNS_DIR)), name="static")
