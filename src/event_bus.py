"""Thread-local event bus for pushing agent events during a campaign run.

Agents and llm.py push events here during execution.
api.py reads them for SSE streaming and saves them to disk for later review.
"""

import threading
from datetime import datetime

_context = threading.local()

# Shared job store — imported and used by both api.py and event_bus
jobs: dict[str, dict] = {}


def set_job(job_id: str):
    """Set the active job ID for the current thread."""
    _context.job_id = job_id


def get_job() -> str | None:
    """Get the active job ID for the current thread."""
    return getattr(_context, "job_id", None)


def push(node: str, event_type: str, message: str, data: dict = None):
    """Push an event to the active job's event list.

    Args:
        node:       Agent name (researcher, copywriter, etc.)
        event_type: "node_done" | "llm_call" | "llm_response" | "error"
        message:    Short human-readable description
        data:       Optional extra payload
    """
    job_id = get_job()
    if not job_id or job_id not in jobs:
        return
    jobs[job_id]["events"].append({
        "node": node,
        "type": event_type,
        "message": message,
        "timestamp": datetime.now().isoformat(),
        "data": data or {},
    })
