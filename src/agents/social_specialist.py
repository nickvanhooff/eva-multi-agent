"""Social Specialist agent node — platform-specific social content."""

from src.llm import call_llm
from src.skills.skills_config import get_skills
from src.state import CampaignState

_BASE_PROMPT = """Je bent een social media specialist voor een reclamebureau.
Je taak is om platformspecifieke social media content te maken op basis van de strategie en marketingteksten.

Als je feedback hebt ontvangen van de Campaign Manager, verwerk die feedback in een verbeterde versie.

Schrijf in het Nederlands. Pas je stijl aan per platform."""


def social_specialist_node(state: CampaignState) -> dict:
    """Create platform-specific social media content.

    Reads: product_description, target_audience, strategy, copy_draft, cm_feedback
    Writes: social_content, social_versions
    """
    feedback = state.get("cm_feedback", "")

    campaign_type = state.get("campaign_type", "product")
    skill_content = get_skills(campaign_type, "social_media")
    system_prompt = (skill_content + "\n\n---\n\n" if skill_content else "") + _BASE_PROMPT

    print("\n" + "=" * 60)
    print("[SOCIAL SPECIALIST] Creating social media content...")
    if feedback and state.get("phase") == "social_review":
        print(f"[SOCIAL SPECIALIST] Feedback received: {feedback[:200]}...")
    print("=" * 60)

    feedback_section = ""
    if feedback and state.get("phase") == "social_review":
        feedback_section = f"""

FEEDBACK VAN CAMPAIGN MANAGER (verwerk dit in je nieuwe versie):
{feedback}"""

    user_prompt = f"""Maak social media content voor het volgende product.

PRODUCT: {state["product_description"]}

DOELGROEP: {state.get("target_audience", "Niet beschikbaar")}

STRATEGIE: {state.get("strategy", "Niet beschikbaar")}

MARKETINGTEKST (als basis): {state.get("copy_draft", "Niet beschikbaar")}
{feedback_section}

Lever content op voor:
1. Instagram (caption + hashtags)
2. LinkedIn (professionele post)
3. X/Twitter (kort en krachtig, max 280 tekens)"""

    response = call_llm(system_prompt, user_prompt, temperature=0.8, provider="openrouter", model="nvidia/nemotron-3-nano-30b-a3b:free")

    print("\n[SOCIAL SPECIALIST] Response received:")
    print("-" * 40)
    print(response[:500] + ("..." if len(response) > 500 else ""))
    print("-" * 40)

    return {
        "social_content": response,
        "social_versions": [response],  # reducer appends to list
    }
