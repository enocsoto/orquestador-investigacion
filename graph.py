from langgraph.graph import END, START, StateGraph

from agents.analyst_agent import analyst_node
from agents.research_agent import research_node
from agents.supervisor import route, supervisor_node
from state import OrchestratorState


def build_graph():
    graph = StateGraph(OrchestratorState)
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("research", research_node)
    graph.add_node("analyst", analyst_node)
    graph.add_edge(START, "supervisor")
    graph.add_conditional_edges(
        "supervisor",
        route,
        {"research": "research", "analyst": "analyst", "finish": END},
    )
    graph.add_edge("research", "supervisor")
    graph.add_edge("analyst", "supervisor")
    return graph.compile()
