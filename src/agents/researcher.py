"""Researcher agent node — product and market analysis."""

from src.llm import call_llm
from src.skills import load_skill
from src.state import CampaignState

SYSTEM_PROMPT = load_skill("product-marketing-context", "marketing-ideas") + """

---

Je bent een marktonderzoeker voor een reclamebureau.
Je taak is om een productomschrijving te analyseren en twee dingen op te leveren:

1. MARKTONDERZOEK: Een beknopte analyse van de markt, concurrenten, en kansen.
2. DOELGROEP: Een gedetailleerde beschrijving van de ideale doelgroep (demografie, psychografie, pijnpunten, behoeften).

Schrijf in het Nederlands. Wees specifiek en concreet."""


def researcher_node(state: CampaignState) -> dict:
    """Analyze the product and identify target audience.

    Reads: product_description
    Writes: market_research, target_audience
    """
    print("\n" + "=" * 60)
    print("[RESEARCHER] Starting product & market analysis...")
    print("=" * 60)

    product = state["product_description"]

    user_prompt = f"""Analyseer het volgende product en lever marktonderzoek + doelgroepanalyse op.

Product: {product}

Geef je antwoord in dit formaat:

## MARKTONDERZOEK
[jouw analyse hier]

## DOELGROEP
[jouw doelgroepbeschrijving hier]"""

    response = call_llm(SYSTEM_PROMPT, user_prompt, temperature=0.4, provider="openrouter", model="nvidia/nemotron-3-nano-30b-a3b:free")

    print("\n[RESEARCHER] Response received:")
    print("-" * 40)
    print(response[:500] + ("..." if len(response) > 500 else ""))
    print("-" * 40)

    # Parse sections from response
    market_research = ""
    target_audience = ""

    if "## MARKTONDERZOEK" in response and "## DOELGROEP" in response:
        parts = response.split("## DOELGROEP")
        market_research = parts[0].replace("## MARKTONDERZOEK", "").strip()
        target_audience = parts[1].strip()
    else:
        # Fallback: use full response for both
        market_research = response
        target_audience = response

    return {
        "market_research": market_research,
        "target_audience": target_audience,
    }
