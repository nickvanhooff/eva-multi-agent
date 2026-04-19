"""Tool wrappers — lightweight web search and Wikipedia lookup for agent use."""

from __future__ import annotations


def duckduckgo_search(query: str, max_results: int = 5) -> str:
    """Search DuckDuckGo and return formatted snippets for up to max_results results.

    Use for brand identity research: query for official colors, visual identity,
    style guides, and design conventions of known organizations, sports clubs,
    companies, and public figures.
    """
    try:
        from ddgs import DDGS

        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))

        if not results:
            return "Geen zoekresultaten gevonden."

        lines = []
        for r in results:
            lines.append(f"- {r['title']}: {r['body'][:200]}")
        return "\n".join(lines)
    except Exception as e:
        return f"[DuckDuckGo zoekfout: {e}]"


def wikipedia_summary(query: str, sentences: int = 4) -> str:
    """Return a short Wikipedia summary for a search query."""
    try:
        import wikipedia

        wikipedia.set_lang("nl")
        result = wikipedia.summary(query, sentences=sentences, auto_suggest=True)
        return result
    except Exception:
        try:
            import wikipedia

            wikipedia.set_lang("en")
            result = wikipedia.summary(query, sentences=sentences, auto_suggest=True)
            return result
        except Exception as e:
            return f"[Wikipedia fout: {e}]"
