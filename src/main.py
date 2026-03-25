"""Entry point for the Eva multi-agent marketing campaign generator."""

import json
import sys
import uuid
from datetime import datetime
from pathlib import Path

from src.graph import build_graph
from src.tracing import setup_tracing


def run_campaign(product_description: str) -> dict:
    """Run the full multi-agent campaign pipeline.

    Args:
        product_description: Description of the product to create a campaign for.

    Returns:
        The final state containing all campaign artifacts.
    """
    graph = build_graph()

    # Each run gets a unique thread_id for checkpointing
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}

    initial_state = {
        "product_description": product_description,
        "copy_versions": [],
        "social_versions": [],
        "iteration_count": 0,
        "approved": False,
    }

    # Run the graph
    result = graph.invoke(initial_state, config)
    return result


def save_campaign_report(result: dict, product_description: str) -> str:
    """Save campaign result to a JSON file.

    Args:
        result: The campaign result from run_campaign()
        product_description: The original product description

    Returns:
        Path to the saved report file
    """
    output_dir = Path("campaigns")
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"campaign_{timestamp}.json"
    filepath = output_dir / filename

    report = {
        "timestamp": datetime.now().isoformat(),
        "product_description": product_description,
        "target_audience": result.get("target_audience", ""),
        "strategy": result.get("strategy", ""),
        "positioning": result.get("positioning", ""),
        "tone_of_voice": result.get("tone_of_voice", ""),
        "copy_draft": result.get("copy_draft", ""),
        "copy_versions_count": len(result.get("copy_versions", [])),
        "social_content": result.get("social_content", ""),
        "social_versions_count": len(result.get("social_versions", [])),
        "iterations": result.get("iteration_count", 0),
        "approved_by_cm": result.get("approved", False),
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    return str(filepath)


def main():
    # Fix UTF-8 output on Windows
    sys.stdout.reconfigure(encoding="utf-8")

    # Setup LangSmith tracing (if enabled)
    setup_tracing()

    # Demo product
    product = """Eco-Cup Go: Een herbruikbare, opvouwbare koffiebeker gemaakt van
    gerecycled oceaanplastic. De beker houdt dranken 4 uur warm, past in je jaszak
    als hij is opgevouwen, en is verkrijgbaar in 5 kleuren. Prijs: EUR 24,95.
    Doelmarkt: milieubewuste professionals (25-45 jaar) in Nederland."""

    print("=" * 60)
    print("EVA MULTI-AGENT MARKETING CAMPAIGN GENERATOR")
    print("=" * 60)
    print(f"\nProduct: {product.strip()}\n")
    print("Starting campaign generation...\n")

    result = run_campaign(product)

    # Print results
    print("\n" + "=" * 60)
    print("CAMPAIGN RESULTS")
    print("=" * 60)

    if result.get("final_campaign"):
        campaign = result["final_campaign"]
        print(f"\nIterations: {campaign.get('iterations', 'N/A')}")
        print(f"Approved by CM: {campaign.get('approved_by_cm', False)}")

    print(f"\n--- DOELGROEP ---\n{result.get('target_audience', 'N/A')}")
    print(f"\n--- STRATEGIE ---\n{result.get('strategy', 'N/A')}")
    print(f"\n--- MARKETINGTEKST ---\n{result.get('copy_draft', 'N/A')}")
    print(f"\n--- SOCIAL CONTENT ---\n{result.get('social_content', 'N/A')}")
    print(f"\n--- VERSIES ---")
    print(f"Copy versies: {len(result.get('copy_versions', []))}")
    print(f"Social versies: {len(result.get('social_versions', []))}")

    # Save campaign report
    report_path = save_campaign_report(result, product)
    print(f"\n" + "=" * 60)
    print(f"📄 Campaign report saved to: {report_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
