"""Website generator — produces a Tailwind HTML landing page from campaign content."""

import re
from datetime import datetime
from pathlib import Path

from src.llm import call_llm, get_agent_config
from src.skills.skills_config import get_skills

_BASE_PROMPT = """You are an expert frontend developer and visual designer.
Your task: generate a complete, production-grade HTML landing page for the campaign below.

FOLLOW THE SKILL INSTRUCTIONS EXACTLY. They contain:
- 5 aesthetic presets with copy-paste CSS (variables + Google Fonts) — pick ONE based on the campaign tone
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


def _strip_fences(text: str) -> str:
    """Remove markdown code fences if the LLM wrapped the output anyway."""
    text = text.strip()
    # Remove ```html ... ``` or ``` ... ```
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

Remember: output raw HTML only. Start with <!DOCTYPE html>."""

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
