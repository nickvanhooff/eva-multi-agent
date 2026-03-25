"""Entry point for the Eva multi-agent marketing campaign generator."""

import sys
import uuid

from src.graph import build_graph


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


def main():
    # Fix UTF-8 output on Windows
    sys.stdout.reconfigure(encoding="utf-8")

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


if __name__ == "__main__":
    main()
