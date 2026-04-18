"""Researcher agent node — product and market analysis."""

from src.llm import call_llm, get_agent_config
from src.skills.skills_config import get_skills
from src.state import CampaignState
from src.tools import duckduckgo_search, wikipedia_summary

_BASE_PROMPT = """
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

    campaign_type = state.get("campaign_type", "product")
    skill_content = get_skills(campaign_type, "researcher")
    system_prompt = (skill_content + "\n\n---\n\n" if skill_content else "") + _BASE_PROMPT

    product = state["product_description"]
    pdf_sources = state.get("pdf_sources", [])

    print("[RESEARCHER] Fetching live data via tools...")
    search_query = product if not pdf_sources else f"{product} {pdf_sources[0]['text'][:80]}"
    search_results = duckduckgo_search(f"{search_query} markt concurrenten doelgroep")
    wiki_results = wikipedia_summary(product)
    print(f"[RESEARCHER] DuckDuckGo: {len(search_results)} chars | Wikipedia: {len(wiki_results)} chars")

    if pdf_sources:
        print(f"[RESEARCHER] {len(pdf_sources)} PDF passages available: using as primary source")
        parts = []
        for i, s in enumerate(pdf_sources):
            page_label = f" (pagina {s['page'] + 1})" if s['page'] is not None else ""
            parts.append(f"[Passage {i+1}]{page_label}\n{s['text']}")
        numbered = "\n\n".join(parts)
        user_prompt = f"""Je hebt de volgende PDF-documentatie ontvangen over het product. Dit is de gezaghebbende bron: de campagne gaat over wat er in de PDF staat, niet over de productomschrijving alleen.

PDF-documentatie (primaire bron):
{numbered}

Productomschrijving (aanvullende context): {product}

Actuele zoekresultaten (DuckDuckGo):
{search_results}

Achtergrondkennis (Wikipedia):
{wiki_results}

Lever marktonderzoek + doelgroepanalyse op. Baseer je primair op de PDF. Voeg na elke claim die direct uit de PDF komt een bronverwijzing toe: [Bron: N] waarbij N het passage-nummer is.

## MARKTONDERZOEK
[jouw analyse hier]

## DOELGROEP
[jouw doelgroepbeschrijving hier]"""
    else:
        print("[RESEARCHER] No PDF context — using product description only")
        user_prompt = f"""Analyseer het volgende product en lever marktonderzoek + doelgroepanalyse op.

Product: {product}

Actuele zoekresultaten (DuckDuckGo):
{search_results}

Achtergrondkennis (Wikipedia):
{wiki_results}

Gebruik bovenstaande brondata als basis voor je analyse. Geef je antwoord in dit formaat:

## MARKTONDERZOEK
[jouw analyse hier]

## DOELGROEP
[jouw doelgroepbeschrijving hier]"""

    response = call_llm(system_prompt, user_prompt, **get_agent_config("researcher"))

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
