"""Skill loader — reads skill markdown files and injects them into agent system prompts."""

from pathlib import Path

SKILLS_DIR = Path(__file__).parent


def load_skill(*skill_names: str) -> str:
    """Load one or more skill files and return combined content."""
    parts = []
    for name in skill_names:
        path = SKILLS_DIR / f"{name}.md"
        if path.exists():
            parts.append(path.read_text(encoding="utf-8").strip())
    return "\n\n---\n\n".join(parts)
