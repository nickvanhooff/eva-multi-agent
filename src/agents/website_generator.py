"""Website generator — produces a Tailwind HTML landing page from campaign content."""

import json
import re
from datetime import datetime
from pathlib import Path

from src.llm import call_llm, get_agent_config
from src.skills.skills_config import get_skills
from src.tools import duckduckgo_search, wikipedia_summary

_ENTITY_IDENTIFICATION_SYSTEM_PROMPT = """You are a brand identity analyst. Analyze the marketing campaign brief and determine whether it references a real, publicly known entity (sports club, company, brand, artist, NGO, etc.) with a documented visual identity.

Respond ONLY with a JSON object — no prose, no markdown fences:

{
  "entity_found": true or false,
  "entity_name": "canonical name e.g. PSV Eindhoven, Apple Inc., Gucci — or null",
  "entity_type": "sports_club | luxury | brand | tech | ngo | government | person | other — or null",
  "search_queries": ["query 1 for brand colors", "query 2 for visual identity"],
  "initial_color_direction": "one sentence on expected colors from your knowledge — or unknown"
}

Rules:
- entity_found true ONLY for real named organizations/brands with a public visual identity.
- Generic or unnamed products: entity_found false, search_queries empty list [].
- search_queries: exactly 2 queries useful for finding official colors/branding. Empty list [] if entity_found false.
- Keep entity_name in its canonical form (usually English or the brand's own language)."""

_DESIGN_REFINEMENT_SYSTEM_PROMPT = """You are a senior visual designer creating a design specification for a marketing landing page. You have been given brand research results for a real organization. Produce a concrete design specification.

Respond ONLY with a JSON object — no prose, no markdown fences:

{
  "primary_bg": "#hexcode",
  "primary_accent": "#hexcode",
  "secondary_accent": "#hexcode",
  "ink": "#hexcode",
  "surface": "#hexcode",
  "preset_base": "EDITORIAL | BOLD | ORGANIC | DARK TECH | WARM STORY",
  "typography_note": "one sentence on font style e.g. Bold sans-serif for impact",
  "design_rationale": "one sentence explaining why these colors match the brand"
}

Rules:
- primary_accent: the brand's signature color used for buttons, labels, and CTAs.
- preset_base: choose based on brand personality (sports_club → BOLD, luxury → EDITORIAL, tech → DARK TECH, etc.)
- All hex codes must be valid 6-digit #rrggbb values.
- If research is inconclusive, use tasteful values appropriate for the entity_type."""

_BASE_PROMPT = """You are an expert frontend developer and visual designer.
Your task: generate a complete, production-grade HTML landing page for the campaign below.

FOLLOW THE SKILL INSTRUCTIONS EXACTLY. They contain:
- A DESIGN BRIEF section (if provided) — follow its hex codes and preset base EXACTLY
- 5 aesthetic presets with copy-paste CSS (variables + Google Fonts) — pick ONE if no brief provided
- Required CSS block (animations, nav, hero, cards, testimonial, CTA, footer)
- Required JavaScript (sticky nav, IntersectionObserver reveals)
- HTML structure template to follow

OUTPUT RULES (non-negotiable):
- Output ONLY raw HTML. Zero markdown. Zero code fences. Zero explanation.
- First character of your response: < (from <!DOCTYPE html>)
- CSS in <style> block in <head>. JS in <script> at end of <body>.
- Include Tailwind CDN + Google Fonts from your chosen preset.
- Placeholder images: https://placehold.co/WxH/BGHEX/TEXTHEX?text=Description
  Use your chosen palette's accent/bg hex values, not always 1e293b/ffffff.

ADAPT all content, copy, and labels from the campaign data provided below.
Write in the same language as the copy_draft."""


def _parse_json_response(text: str) -> dict | None:
    """Strip markdown fences and parse first JSON object from LLM response."""
    text = re.sub(r"^```(?:json)?\s*", "", text.strip(), flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text).strip()
    start, end = text.find("{"), text.rfind("}") + 1
    if start == -1 or end == 0:
        return None
    try:
        return json.loads(text[start:end])
    except json.JSONDecodeError:
        return None


def _build_fallback_brief(entity_name: str, initial_color_direction: str, identification: dict) -> str:
    """Minimal brief when tool calls fail but entity was identified via LLM knowledge."""
    preset_map = {
        "sports_club": "BOLD", "luxury": "EDITORIAL", "tech": "DARK TECH",
        "brand": "BOLD", "ngo": "WARM STORY", "government": "EDITORIAL",
        "person": "WARM STORY", "other": "BOLD",
    }
    preset = preset_map.get(identification.get("entity_type", "other"), "BOLD")
    return (
        f"DESIGN BRIEF\nEntity: {entity_name}\n"
        f"Note: Brand search unavailable. Apply best judgment based on known identity.\n"
        f"Color direction: {initial_color_direction}\n"
        f"Preset base for layout/typography: {preset}\n"
        f"INSTRUCTION: Use colors consistent with {entity_name}'s known brand identity. "
        f"Do NOT default to generic grey or random accent colors."
    )


def _format_design_brief(entity_name: str, spec: dict) -> str:
    """Serialize a parsed design spec dict into the DESIGN BRIEF string for prompt injection."""
    return (
        f"DESIGN BRIEF\nEntity: {entity_name}\n"
        f"Background color (--bg): {spec.get('primary_bg', '#ffffff')}\n"
        f"Primary accent (--accent): {spec.get('primary_accent', '#cc0000')}\n"
        f"Secondary accent (--accent-alt): {spec.get('secondary_accent', '#1a1a1a')}\n"
        f"Text color (--ink): {spec.get('ink', '#111111')}\n"
        f"Surface color (--surface): {spec.get('surface', '#f5f5f5')}\n"
        f"Preset base for layout/typography: {spec.get('preset_base', 'BOLD')}\n"
        f"Typography: {spec.get('typography_note', '')}\n"
        f"Rationale: {spec.get('design_rationale', '')}\n"
        f"INSTRUCTION: These hex values are NON-NEGOTIABLE. Apply them to CSS :root variables exactly. "
        f"Do not substitute preset defaults. The preset base above is used ONLY for font and layout "
        f"structure — its color variables are overridden by this brief."
    )


def _research_design_direction(campaign_data: dict) -> str:
    """Phase 1: identify known entity, optionally search for brand colors, return design brief.

    Flow:
    1. LLM call 1 — entity identification (always runs, fast)
    2. Tool calls — duckduckgo_search + wikipedia_summary (only if entity found)
    3. LLM call 2 — design refinement using search results (only if searches succeeded)

    Returns a DESIGN BRIEF string ready for injection into the HTML generation prompt.
    Returns empty string on any failure — generate_website degrades to preset-only behavior.
    """
    print("[WEBSITE GENERATOR] Phase 1: Design research starting...")

    # --- LLM call 1: entity identification ---
    id_user_prompt = (
        f"PRODUCT: {campaign_data.get('product_description', '')}\n"
        f"TARGET AUDIENCE: {campaign_data.get('target_audience', '')}\n"
        f"POSITIONING: {campaign_data.get('positioning', '')}\n"
        f"TONE OF VOICE: {campaign_data.get('tone_of_voice', '')}\n"
        f"COPY EXCERPT: {str(campaign_data.get('copy_draft', ''))[:400]}"
    )
    try:
        raw = call_llm(
            _ENTITY_IDENTIFICATION_SYSTEM_PROMPT,
            id_user_prompt,
            **get_agent_config("website_generator"),
        )
    except Exception as e:
        print(f"[WEBSITE GENERATOR] Entity identification failed: {e} — skipping research")
        return ""

    identification = _parse_json_response(raw)
    if not identification or not identification.get("entity_found"):
        print("[WEBSITE GENERATOR] No known entity — using preset selection only")
        return ""

    entity_name = identification.get("entity_name", "")
    search_queries = identification.get("search_queries", [])
    initial_color_direction = identification.get("initial_color_direction", "unknown")
    print(f"[WEBSITE GENERATOR] Entity detected: {entity_name} — running brand identity search...")

    # --- Tool calls (only when entity found) ---
    snippets = []
    for query in search_queries[:2]:
        try:
            result = duckduckgo_search(f"{query} brand colors visual identity", max_results=3)
            if result and not result.startswith("[DuckDuckGo"):
                snippets.append(f"Search: {query!r}\n{result}")
        except Exception as e:
            print(f"[WEBSITE GENERATOR] DuckDuckGo failed for {query!r}: {e}")

    try:
        wiki = wikipedia_summary(entity_name, sentences=4)
        if wiki and not wiki.startswith("[Wikipedia"):
            snippets.append(f"Wikipedia: {entity_name}\n{wiki}")
    except Exception as e:
        print(f"[WEBSITE GENERATOR] Wikipedia failed for {entity_name!r}: {e}")

    if not snippets:
        print("[WEBSITE GENERATOR] All searches failed — using fallback brief from prior knowledge")
        return _build_fallback_brief(entity_name, initial_color_direction, identification)

    # --- LLM call 2: design refinement using real search data ---
    refinement_prompt = (
        f"Brand: {entity_name}\n"
        f"Entity type: {identification.get('entity_type', 'unknown')}\n"
        f"Initial color direction (prior knowledge): {initial_color_direction}\n\n"
        f"Brand research results:\n" + "\n\n".join(snippets)
    )
    try:
        raw2 = call_llm(
            _DESIGN_REFINEMENT_SYSTEM_PROMPT,
            refinement_prompt,
            **{**get_agent_config("website_generator"), "temperature": 0.3},
        )
    except Exception as e:
        print(f"[WEBSITE GENERATOR] Design refinement failed: {e} — using fallback brief")
        return _build_fallback_brief(entity_name, initial_color_direction, identification)

    spec = _parse_json_response(raw2)
    if not spec:
        print("[WEBSITE GENERATOR] Could not parse design spec — using fallback brief")
        return _build_fallback_brief(entity_name, initial_color_direction, identification)

    print(f"[WEBSITE GENERATOR] Design brief ready: accent={spec.get('primary_accent')} preset={spec.get('preset_base')}")
    return _format_design_brief(entity_name, spec)


def _strip_fences(text: str) -> str:
    """Remove markdown code fences if the LLM wrapped the output anyway."""
    text = text.strip()
    text = re.sub(r"^```(?:html)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def generate_website(campaign_data: dict) -> dict:
    """Generate a Tailwind HTML landing page from campaign content.

    Args:
        campaign_data: Dict with keys: copy_draft, social_content, target_audience,
                       tone_of_voice, positioning, product_description, campaign_type.

    Returns:
        {"html_content": str, "html_path": str}
        html_path is relative: "campaigns/websites/{filename}.html"
    """
    campaign_type = campaign_data.get("campaign_type", "product")
    skill_content = get_skills(campaign_type, "website_generator")
    system_prompt = (skill_content + "\n\n---\n\n" if skill_content else "") + _BASE_PROMPT

    print("\n" + "=" * 60)
    print("[WEBSITE GENERATOR] Building HTML landing page...")
    print("=" * 60)

    # Phase 1: design research — identify entity, look up brand colors
    design_brief = _research_design_direction(campaign_data)

    print("\n[WEBSITE GENERATOR] Phase 2: Generating HTML...")

    # Build hero image reference — use the generated campaign image if available,
    # otherwise fall back to placehold.co. The HTML lives at campaigns/websites/,
    # served at /static/websites/, so ../images/ resolves to /static/images/.
    raw_image_path = campaign_data.get("image_path") or campaign_data.get("image_url")
    if raw_image_path:
        image_filename = Path(raw_image_path).name
        hero_image_url = f"../images/{image_filename}"
        image_instruction = (
            f'CAMPAIGN IMAGE: Use this real image for the hero section: <img src="{hero_image_url}" ...>\n'
            f'Do NOT use placehold.co for the hero — only for secondary/background images if needed.'
        )
    else:
        hero_image_url = None
        image_instruction = (
            "No campaign image available. Use placehold.co for all images, "
            "with colors matching your chosen palette."
        )

    user_prompt = f"""Generate a landing page for this marketing campaign.

PRODUCT: {campaign_data.get('product_description', '')}

TARGET AUDIENCE: {campaign_data.get('target_audience', '')}

POSITIONING: {campaign_data.get('positioning', '')}

TONE OF VOICE: {campaign_data.get('tone_of_voice', '')}

MARKETING COPY (use this as the main content):
{campaign_data.get('copy_draft', '')}

SOCIAL CONTENT (use quotes from this for testimonials):
{campaign_data.get('social_content', '')}

{image_instruction}
"""

    # Inject design brief after image instruction, before output rule (recency advantage)
    if design_brief:
        user_prompt += f"\n{design_brief}\n"

    user_prompt += "\nRemember: output raw HTML only. Start with <!DOCTYPE html>."

    response = call_llm(system_prompt, user_prompt, **get_agent_config("website_generator"))
    html_content = _strip_fences(response)

    output_dir = Path("campaigns/websites")
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"campaign_{timestamp}.html"
    html_path = str(output_dir / filename)

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"[WEBSITE GENERATOR] HTML saved: {html_path} ({len(html_content)} chars)")

    return {
        "html_content": html_content,
        "html_path": html_path,
    }
