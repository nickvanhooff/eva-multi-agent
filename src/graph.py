"""LangGraph StateGraph assembly for the Eva multi-agent system."""

from langgraph.graph import END, START, StateGraph
from langgraph.checkpoint.memory import MemorySaver

from src.state import CampaignState
from src.rag import retrieve_pdf_context
from src.agents.researcher import researcher_node
from src.agents.strategist import strateeg_node
from src.agents.copywriter import copywriter_node
from src.agents.social_specialist import social_specialist_node
from src.agents.campaign_manager import campaign_manager_node, cm_router
from src.agents.image_generator import image_generator_node


def pdf_ingestion_node(state: CampaignState) -> dict:
    """RAG node — ingest PDF and store retrieved context in state.

    Runs before the Researcher. If no pdf_path is set, skips silently.

    Reads:  pdf_path
    Writes: pdf_context
    """
    pdf_path = state.get("pdf_path")
    if not pdf_path:
        print("[PDF INGESTION] No pdf_path provided — skipping RAG")
        return {"pdf_context": ""}

    print("\n" + "=" * 60)
    print("[PDF INGESTION] Starting PDF ingestion via RAG...")
    print("=" * 60)

    campaign_type = state.get("campaign_type", "product")
    pdf_context = retrieve_pdf_context(pdf_path, campaign_type=campaign_type)
    return {"pdf_context": pdf_context}


def build_graph():
    """Build and compile the full multi-agent graph with RAG support.

    Flow: START -> PDF Ingestion -> Researcher -> Strateeg -> Copywriter
          -> Social Specialist -> Campaign Manager (conditional) -> Image Generator -> END
    """
    graph = StateGraph(CampaignState)

    # Register all nodes — pdf_ingestion runs first
    graph.add_node("pdf_ingestion", pdf_ingestion_node)
    graph.add_node("researcher", researcher_node)
    graph.add_node("strateeg", strateeg_node)
    graph.add_node("copywriter", copywriter_node)
    graph.add_node("social_specialist", social_specialist_node)
    graph.add_node("campaign_manager", campaign_manager_node)
    graph.add_node("image_generator", image_generator_node)

    # Linear edges: the main pipeline
    graph.add_edge(START, "pdf_ingestion")
    graph.add_edge("pdf_ingestion", "researcher")
    graph.add_edge("researcher", "strateeg")
    graph.add_edge("strateeg", "copywriter")
    graph.add_edge("copywriter", "social_specialist")
    graph.add_edge("social_specialist", "campaign_manager")

    # Conditional routing from Campaign Manager
    graph.add_conditional_edges(
        "campaign_manager",
        cm_router,
        {
            "copywriter": "copywriter",
            "social_specialist": "social_specialist",
            "finalize": "image_generator",
        },
    )
    graph.add_edge("image_generator", END)

    # Compile with checkpointer for state persistence
    checkpointer = MemorySaver()
    return graph.compile(checkpointer=checkpointer)
