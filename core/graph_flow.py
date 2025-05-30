"""
Graph flow creation and configuration.
"""

from langgraph.graph import StateGraph, START, END
from .nodes import (optimize_prompt, generate_code,
                    execute_code, should_continue)
from .state_models import GraphState


def create_graph_flow() -> StateGraph:
    """
    Create and configure the AI code agent's graph.

    Returns:
        Compiled StateGraph ready for execution
    """
    graph_flow = StateGraph(GraphState)

    graph_flow.add_node("optimize_prompt", optimize_prompt)
    graph_flow.add_node("generate_code", generate_code)
    graph_flow.add_node("execute_code", execute_code)

    graph_flow.add_edge(START, "optimize_prompt")
    graph_flow.add_edge("optimize_prompt", "generate_code")

    graph_flow.add_conditional_edges(
        "generate_code",
        lambda x: "retry" if x.get("error_message") else "continue",
        {
            "continue": "execute_code",
            "retry": END
        }
    )

    graph_flow.add_conditional_edges(
        "execute_code",
        should_continue,
        {
            "end": END,
            "retry": "generate_code",
        },
    )

    return graph_flow.compile()
