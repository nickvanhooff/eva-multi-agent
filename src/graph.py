"""LangGraph StateGraph assembly for the Eva multi-agent system."""

from langgraph.graph import END, START, StateGraph
from langgraph.checkpoint.memory import MemorySaver

from src.state import CampaignState
from src.agents.researcher import researcher_node
from src.agents.strategist import strateeg_node


def build_graph():
    """Build and compile the multi-agent graph.

    Currently a minimal 2-node graph: Researcher -> Strateeg.
    Will be expanded with Copywriter, Social Specialist, and Campaign Manager.
    """
    graph = StateGraph(CampaignState)

    # Register nodes
    graph.add_node("researcher", researcher_node)
    graph.add_node("strateeg", strateeg_node)

    # Linear edges
    graph.add_edge(START, "researcher")
    graph.add_edge("researcher", "strateeg")
    graph.add_edge("strateeg", END)

    # Compile with checkpointer for state persistence
    checkpointer = MemorySaver()
    return graph.compile(checkpointer=checkpointer)
