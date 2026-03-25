"""LangGraph StateGraph assembly for the Eva multi-agent system."""

from langgraph.graph import END, START, StateGraph
from langgraph.checkpoint.memory import MemorySaver

from src.state import CampaignState
from src.agents.researcher import researcher_node
from src.agents.strategist import strateeg_node
from src.agents.copywriter import copywriter_node
from src.agents.social_specialist import social_specialist_node
from src.agents.campaign_manager import campaign_manager_node, cm_router


def build_graph():
    """Build and compile the full 5-agent multi-agent graph.

    Flow: START -> Researcher -> Strateeg -> Copywriter -> Social Specialist -> Campaign Manager
    Campaign Manager routes conditionally: back to Copywriter/Social Specialist or to END.
    """
    graph = StateGraph(CampaignState)

    # Register all 5 agent nodes
    graph.add_node("researcher", researcher_node)
    graph.add_node("strateeg", strateeg_node)
    graph.add_node("copywriter", copywriter_node)
    graph.add_node("social_specialist", social_specialist_node)
    graph.add_node("campaign_manager", campaign_manager_node)

    # Linear edges: the main pipeline
    graph.add_edge(START, "researcher")
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
            "finalize": END,
        },
    )

    # Compile with checkpointer for state persistence
    checkpointer = MemorySaver()
    return graph.compile(checkpointer=checkpointer)
