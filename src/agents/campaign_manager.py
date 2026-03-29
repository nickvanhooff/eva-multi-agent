"""Campaign Manager agent node — coordination, QA, and routing decisions."""

import re

from src.llm import call_llm, get_agent_config
from src.skills.skills_config import get_skills
from src.state import CampaignState

_BASE_PROMPT = """Je bent de Campaign Manager van een reclamebureau.
Je taak is om de kwaliteit van de marketingcampagne te beoordelen.

Beoordeel de marketingteksten en social media content op:
- Aansluiting bij de strategie en doelgroep
- Consistentie in tone of voice
- Creativiteit en overtuigingskracht
- Volledigheid van de campagne

Geef je oordeel in dit formaat:
BESLISSING: GOEDGEKEURD of AFGEWEZEN
FASE: copy_review of social_review of final
FEEDBACK: [jouw feedback hier]

Wees streng maar constructief. Geef specifieke, actionable feedback."""


MAX_ITERATIONS = 3


def campaign_manager_node(state: CampaignState) -> dict:
    """Evaluate campaign quality and decide on approval or revision.

    Reads: ALL state fields
    Writes: cm_feedback, phase, approved, final_campaign
    """
    iteration = state.get("iteration_count", 0)

    campaign_type = state.get("campaign_type", "product")
    skill_content = get_skills(campaign_type, "campaign_manager")
    system_prompt = (skill_content + "\n\n---\n\n" if skill_content else "") + _BASE_PROMPT

    print("\n" + "=" * 60)
    print(f"[CAMPAIGN MANAGER] Evaluating campaign (iteration {iteration})...")
    print("=" * 60)

    user_prompt = f"""Beoordeel de volgende marketingcampagne:

PRODUCT: {state["product_description"]}

DOELGROEP: {state.get("target_audience", "Niet beschikbaar")}

STRATEGIE: {state.get("strategy", "Niet beschikbaar")}

POSITIONERING: {state.get("positioning", "Niet beschikbaar")}

TONE OF VOICE: {state.get("tone_of_voice", "Niet beschikbaar")}

MARKETINGTEKST:
{state.get("copy_draft", "Niet beschikbaar")}

SOCIAL MEDIA CONTENT:
{state.get("social_content", "Niet beschikbaar")}

ITERATIE: {iteration} van {MAX_ITERATIONS}

Geef je beoordeling met BESLISSING, FASE en FEEDBACK."""

    response = call_llm(system_prompt, user_prompt, **get_agent_config("campaign_manager"))

    print("\n[CAMPAIGN MANAGER] Response received:")
    print("-" * 40)
    print(response[:500] + ("..." if len(response) > 500 else ""))
    print("-" * 40)

    # Parse decision from response
    approved = False
    phase = "final"
    feedback = response

    # Extract BESLISSING
    decision_match = re.search(r"BESLISSING:\s*(GOEDGEKEURD|AFGEWEZEN)", response, re.IGNORECASE)
    if decision_match:
        approved = decision_match.group(1).upper() == "GOEDGEKEURD"

    # Extract FASE
    phase_match = re.search(r"FASE:\s*(copy_review|social_review|final)", response, re.IGNORECASE)
    if phase_match:
        phase = phase_match.group(1).lower()

    # Extract FEEDBACK
    feedback_match = re.search(r"FEEDBACK:\s*(.+)", response, re.DOTALL | re.IGNORECASE)
    if feedback_match:
        feedback = feedback_match.group(1).strip()

    print(f"\n[CAMPAIGN MANAGER] Decision: {'GOEDGEKEURD' if approved else 'AFGEWEZEN'}")
    print(f"[CAMPAIGN MANAGER] Phase: {phase}")
    print(f"[CAMPAIGN MANAGER] Feedback: {feedback[:200]}...")

    result = {
        "cm_feedback": feedback,
        "phase": phase,
        "approved": approved,
    }

    # If approved or max iterations reached, create final campaign
    if approved or iteration >= MAX_ITERATIONS:
        result["approved"] = True
        result["final_campaign"] = {
            "product": state["product_description"],
            "target_audience": state.get("target_audience", ""),
            "strategy": state.get("strategy", ""),
            "positioning": state.get("positioning", ""),
            "tone_of_voice": state.get("tone_of_voice", ""),
            "copy": state.get("copy_draft", ""),
            "social_content": state.get("social_content", ""),
            "iterations": iteration,
            "approved_by_cm": approved,
        }

    return result


def cm_router(state: CampaignState) -> str:
    """Route based on Campaign Manager's decision.

    Returns:
        "copywriter" — send back for copy revision
        "social_specialist" — send back for social revision
        "finalize" — approve and end
    """
    if state.get("approved", False):
        print("[ROUTER] -> END (approved)")
        return "finalize"
    if state.get("iteration_count", 0) >= MAX_ITERATIONS:
        print("[ROUTER] -> END (max iterations reached)")
        return "finalize"

    phase = state.get("phase", "copy_review")
    if phase == "social_review":
        print("[ROUTER] -> SOCIAL SPECIALIST (feedback loop)")
        return "social_specialist"

    # Default: send back to copywriter (covers copy_review + unexpected phase values)
    print("[ROUTER] -> COPYWRITER (feedback loop)")
    return "copywriter"
