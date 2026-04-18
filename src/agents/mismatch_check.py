"""Mismatch check node — detects if the product description conflicts with the PDF content.

If a mismatch is detected, the graph is interrupted and the user is asked to confirm
or correct the product description before the campaign continues.
"""

import json
import re

from langgraph.types import interrupt

from src.llm import call_llm, get_agent_config
from src.state import CampaignState


def _parse_response(response: str) -> tuple[bool, str]:
    """Parse LLM JSON response into (match, pdf_subject). Fails safe to match=True."""
    try:
        json_match = re.search(r'\{.*?\}', response, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            return bool(data.get("match", True)), str(data.get("pdf_subject", ""))
    except (json.JSONDecodeError, AttributeError):
        pass
    # Fallback: no mismatch assumed
    return True, ""


def mismatch_check_node(state: CampaignState) -> dict:
    """Compare product description with PDF subject. Interrupt if they conflict.

    Reads:  pdf_sources, product_description
    Writes: product_description (only if user provides a correction)
    """
    pdf_sources = state.get("pdf_sources", [])
    if not pdf_sources:
        return {}  # no PDF uploaded, skip

    description = state["product_description"]
    subject_passage = pdf_sources[0]["text"][:500]  # first passage = subject query result

    print("[MISMATCH CHECK] Comparing description with PDF subject...")

    response = call_llm(
        system_prompt=(
            "Je controleert of een productomschrijving overeenkomt met de inhoud van een PDF. "
            "Antwoord uitsluitend met geldig JSON, geen uitleg: "
            "{\"match\": true/false, \"pdf_subject\": \"korte omschrijving van het PDF-onderwerp\"}"
        ),
        user_prompt=(
            f"Productomschrijving: {description}\n\n"
            f"Eerste passage uit de PDF:\n{subject_passage}"
        ),
        **get_agent_config("researcher"),
    )

    match, pdf_subject = _parse_response(response)

    if match:
        print(f"[MISMATCH CHECK] OK: description matches PDF ('{pdf_subject}')")
        return {}

    print(f"[MISMATCH CHECK] Mismatch detected: description='{description}', pdf='{pdf_subject}'")

    corrected = interrupt({
        "type": "mismatch",
        "question": (
            f"De PDF gaat over '{pdf_subject}', maar de productomschrijving zegt '{description}'. "
            f"Welke omschrijving wil je gebruiken voor de campagne?"
        ),
        "original": description,
        "suggestion": pdf_subject,
    })

    return {"product_description": corrected}
