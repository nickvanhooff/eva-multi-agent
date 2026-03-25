"""Campaign state definition for the Eva multi-agent system."""

import operator
from typing import Annotated, Optional, TypedDict


class CampaignState(TypedDict):
    """Shared state across all agent nodes.

    Each agent reads relevant fields and returns only the fields it writes.
    LangGraph merges the returned dict into this state automatically.
    """

    # --- Input ---
    product_description: str

    # --- Researcher output ---
    market_research: str
    target_audience: str

    # --- Strateeg output ---
    strategy: str
    positioning: str
    tone_of_voice: str

    # --- Copywriter output ---
    copy_draft: str
    copy_versions: Annotated[list[str], operator.add]  # reducer: append each iteration

    # --- Social Specialist output ---
    social_content: str
    social_versions: Annotated[list[str], operator.add]  # reducer: append each iteration

    # --- Campaign Manager output ---
    cm_feedback: str
    phase: str  # "copy_review" | "social_review" | "final"
    approved: bool
    iteration_count: int
    final_campaign: Optional[dict]
