"""
agent/graph/graph.py

Assembles and compiles the LangGraph StateGraph for First Cup.

Pipeline:
    scrape → write → publish → notify → email → END

Each node is an async function defined in ``agent.graph.nodes``.
The compiled graph exposes ``ainvoke`` for async execution.
"""

from __future__ import annotations

import structlog
from langgraph.graph import END, StateGraph
from langgraph.graph.graph import CompiledGraph

from agent.graph.nodes import (
    AgentState,
    email_node,
    notify_node,
    publish_node,
    scrape_node,
    write_node,
)

logger = structlog.get_logger(__name__)


def build_graph() -> CompiledGraph:
    """
    Construct, wire, and compile the First Cup LangGraph pipeline.

    Returns:
        A compiled :class:`~langgraph.graph.graph.CompiledGraph` ready for
        ``ainvoke`` / ``invoke`` calls.

    Example::

        graph = build_graph()
        result = await graph.ainvoke(initial_state)
    """
    workflow: StateGraph = StateGraph(AgentState)

    # Register nodes
    workflow.add_node("scrape",  scrape_node)
    workflow.add_node("write",   write_node)
    workflow.add_node("publish", publish_node)
    workflow.add_node("notify",  notify_node)
    workflow.add_node("email",   email_node)

    # Set entry point
    workflow.set_entry_point("scrape")

    # Linear pipeline: scrape → write → publish → notify → email → END
    workflow.add_edge("scrape",  "write")
    workflow.add_edge("write",   "publish")
    workflow.add_edge("publish", "notify")
    workflow.add_edge("notify",  "email")
    workflow.add_edge("email",   END)

    compiled: CompiledGraph = workflow.compile()
    logger.info(
        "graph_compiled",
        nodes=["scrape", "write", "publish", "notify", "email"],
        entry="scrape",
    )
    return compiled
