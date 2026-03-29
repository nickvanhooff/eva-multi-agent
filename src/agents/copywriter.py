"""Copywriter agent node — marketing copy creation and revision."""

from src.llm import call_llm
from src.skills.skills_config import get_skills
from src.state import CampaignState

_BASE_PROMPT = """Je bent een creatieve copywriter voor een reclamebureau.
Je taak is om pakkende marketingteksten te schrijven op basis van de strategie en doelgroep.

Als je feedback hebt ontvangen van de Campaign Manager, verwerk die feedback in een verbeterde versie.

Schrijf in het Nederlands. Wees creatief, pakkend en overtuigend."""


def copywriter_node(state: CampaignState) -> dict:
    """Write or revise marketing copy based on strategy.

    Reads: product_description, target_audience, strategy, tone_of_voice, cm_feedback
    Writes: copy_draft, copy_versions, iteration_count
    """
    feedback = state.get("cm_feedback", "")
    iteration = state.get("iteration_count", 0)

    campaign_type = state.get("campaign_type", "product")
    skill_content = get_skills(campaign_type, "copywriter")
    system_prompt = (skill_content + "\n\n---\n\n" if skill_content else "") + _BASE_PROMPT

    print("\n" + "=" * 60)
    print(f"[COPYWRITER] Writing marketing copy (iteration {iteration + 1})...")
    if feedback and iteration > 0:
        print(f"[COPYWRITER] Feedback received: {feedback[:200]}...")
    print("=" * 60)

    feedback_section = ""
    if feedback and iteration > 0:
        feedback_section = f"""

FEEDBACK VAN CAMPAIGN MANAGER (verwerk dit in je nieuwe versie):
{feedback}"""

    user_prompt = f"""Schrijf marketingteksten voor het volgende product.

PRODUCT: {state["product_description"]}

DOELGROEP: {state.get("target_audience", "Niet beschikbaar")}

STRATEGIE: {state.get("strategy", "Niet beschikbaar")}

TONE OF VOICE: {state.get("tone_of_voice", "Niet beschikbaar")}
{feedback_section}

Lever de volgende teksten op:
1. Een headline (max 10 woorden)
2. Een subheadline (max 20 woorden)
3. Een bodytekst (2-3 alinea's)
4. Een call-to-action"""

    response = call_llm(system_prompt, user_prompt, temperature=0.9, provider="openrouter", model="nvidia/nemotron-3-nano-30b-a3b:free")

    print("\n[COPYWRITER] Response received:")
    print("-" * 40)
    print(response[:500] + ("..." if len(response) > 500 else ""))
    print("-" * 40)

    return {
        "copy_draft": response,
        "copy_versions": [response],  # reducer appends to list
        "iteration_count": iteration + 1,
    }
