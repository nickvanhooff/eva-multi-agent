"""SKILL_MAP — maps campaign_type to per-agent skill lists."""

from src.skills import load_skill

SKILL_MAP: dict[str, dict[str, list[str]]] = {
    "product": {
        "researcher":          ["research-brief"],
        "copywriter":          ["copywriting"],
        "social_media":        ["social-media"],
        "email_marketer":      ["email-marketing"],
        "campaign_manager":    ["launch-strategy"],
        "website_generator":   ["website-generation"],
    },
    "book": {
        "researcher":          ["book-context"],
        "copywriter":          ["book-copywriting"],
        "social_media":        ["book-social"],
        "email_marketer":      ["email-marketing"],
        "campaign_manager":    ["book-launch-strategy"],
        "website_generator":   ["website-generation"],
    },
}


def get_skills(campaign_type: str, agent: str) -> str:
    """Return loaded skill content for a given campaign type and agent.

    Falls back to 'product' if the campaign_type is unknown.
    Returns empty string if agent has no skills defined.
    """
    skills = SKILL_MAP.get(campaign_type, SKILL_MAP["product"])
    skill_names = skills.get(agent, [])
    if not skill_names:
        return ""
    return load_skill(*skill_names)
