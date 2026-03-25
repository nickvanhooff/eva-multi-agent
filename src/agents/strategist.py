"""Strateeg agent node — strategy, positioning, and tone of voice."""

from src.llm import call_llm
from src.state import CampaignState

SYSTEM_PROMPT = """Je bent een marketingstrateeg voor een reclamebureau.
Je taak is om op basis van het marktonderzoek en de doelgroep een marketingstrategie te ontwikkelen.

Je levert drie onderdelen op:
1. STRATEGIE: De overkoepelende marketingstrategie en aanpak.
2. POSITIONERING: Hoe het product zich onderscheidt van concurrenten.
3. TONE OF VOICE: De schrijfstijl en toon voor alle marketinguitingen.

Schrijf in het Nederlands. Wees concreet en actionable."""


def strateeg_node(state: CampaignState) -> dict:
    """Develop marketing strategy based on research.

    Reads: product_description, market_research, target_audience
    Writes: strategy, positioning, tone_of_voice
    """
    print("\n" + "=" * 60)
    print("[STRATEEG] Developing marketing strategy...")
    print("=" * 60)

    user_prompt = f"""Ontwikkel een marketingstrategie op basis van de volgende informatie:

PRODUCT: {state["product_description"]}

MARKTONDERZOEK: {state.get("market_research", "Niet beschikbaar")}

DOELGROEP: {state.get("target_audience", "Niet beschikbaar")}

Geef je antwoord in dit formaat:

## STRATEGIE
[jouw strategie hier]

## POSITIONERING
[jouw positionering hier]

## TONE OF VOICE
[jouw tone of voice hier]"""

    response = call_llm(SYSTEM_PROMPT, user_prompt, temperature=0.5, provider="groq", model="llama-3.1-8b-instant")

    print("\n[STRATEEG] Response received:")
    print("-" * 40)
    print(response[:500] + ("..." if len(response) > 500 else ""))
    print("-" * 40)

    # Parse sections from response
    strategy = ""
    positioning = ""
    tone_of_voice = ""

    sections = {"## STRATEGIE": "", "## POSITIONERING": "", "## TONE OF VOICE": ""}
    current_section = None

    for line in response.split("\n"):
        line_upper = line.strip().upper()
        if "## STRATEGIE" in line_upper:
            current_section = "## STRATEGIE"
        elif "## POSITIONERING" in line_upper:
            current_section = "## POSITIONERING"
        elif "## TONE OF VOICE" in line_upper:
            current_section = "## TONE OF VOICE"
        elif current_section:
            sections[current_section] += line + "\n"

    strategy = sections["## STRATEGIE"].strip() or response
    positioning = sections["## POSITIONERING"].strip() or ""
    tone_of_voice = sections["## TONE OF VOICE"].strip() or ""

    return {
        "strategy": strategy,
        "positioning": positioning,
        "tone_of_voice": tone_of_voice,
    }
