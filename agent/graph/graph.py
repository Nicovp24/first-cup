"""
agent/graph/graph.py

Assembles and compiles the LangGraph StateGraph for Nexus Digest.

Pipeline:
    scrape --> write --> publish --> END

Each node is an async function defined in ``agent.graph.nodes``.
The compiled graph exposes ``ainvoke`` for async execution.
"""

from __future__ import annotations

import structlog
from langgraph.graph import END, StateGraph
from langgraph.graph.graph import CompiledGraph

from agent.graph.nodes import AgentState, notify_node, publish_node, scrape_node, write_node

logger = structlog.get_logger(__name__)


def build_graph() -> CompiledGraph:
    """
    Construct, wire, and compile the Nexus Digest LangGraph pipeline.

    Returns:
        A compiled :class:`~langgraph.graph.graph.CompiledGraph` ready for
        ``ainvoke`` / ``invoke`` calls.

    Example::

        graph = build_graph()
        result = await graph.ainvoke(initial_state)
    """
    workflow: StateGraph = StateGraph(AgentState)

    # Register nodes
    workflow.add_node("scrape", scrape_node)
    workflow.add_node("write", write_node)
    workflow.add_node("publish", publish_node)
    workflow.add_node("notify", notify_node)

    # Set entry point
    workflow.set_entry_point("scrape")

    # Linear pipeline: scrape → write → publish → notify → END
    workflow.add_edge("scrape", "write")
    workflow.add_edge("write", "publish")
    workflow.add_edge("publish", "notify")
    workflow.add_edge("notify", END)

    compiled: CompiledGraph = workflow.compile()
    logger.info(
        "graph_compiled",
        nodes=["scrape", "write", "publish", "notify"],
        entry="scrape",
    )
    return compiled
