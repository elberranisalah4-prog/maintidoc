"""LangGraph Workflow Definition for MAINTIDOC.

Assembles the multi-step agentic graph with Human-In-The-Loop (HITL) interrupt.
"""

import uuid
from typing import Literal
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from src.agent.state import AgentState
from src.agent.nodes import (
    verify_access_node,
    analyze_image_node,
    search_sources_node,
    consult_mcp_node,
    synthesize_response_node,
    prepare_ticket_node,
    create_ticket_mcp_node
)

def route_after_auth(state: AgentState) -> Literal["analyze_image", "__end__"]:
    """Routes to image analysis or terminates immediately if security checks fail."""
    if state.get("injection_detected") or not state.get("rbac_allowed", False):
        return "__end__"
    return "analyze_image"

def route_after_synthesis(state: AgentState) -> Literal["prepare_ticket", "__end__"]:
    """Routes to ticket preparation if requested, otherwise ends."""
    if state.get("status") == "needs_clarification":
        return "__end__"
    if state.get("needs_ticket"):
        return "prepare_ticket"
    return "__end__"

def build_maintidoc_graph(memory_saver: bool = True):
    workflow = StateGraph(AgentState)

    # Add Nodes
    workflow.add_node("verify_access", verify_access_node)
    workflow.add_node("analyze_image", analyze_image_node)
    workflow.add_node("search_sources", search_sources_node)
    workflow.add_node("consult_mcp", consult_mcp_node)
    workflow.add_node("synthesize_response", synthesize_response_node)
    workflow.add_node("prepare_ticket", prepare_ticket_node)
    workflow.add_node("create_ticket_mcp", create_ticket_mcp_node)

    # Add Edges
    workflow.add_edge(START, "verify_access")
    
    workflow.add_conditional_edges(
        "verify_access",
        route_after_auth,
        {
            "analyze_image": "analyze_image",
            "__end__": END
        }
    )

    workflow.add_edge("analyze_image", "search_sources")
    workflow.add_edge("search_sources", "consult_mcp")
    workflow.add_edge("consult_mcp", "synthesize_response")

    workflow.add_conditional_edges(
        "synthesize_response",
        route_after_synthesis,
        {
            "prepare_ticket": "prepare_ticket",
            "__end__": END
        }
    )

    # Note: prepare_ticket is an interruption checkpoint for human approval
    workflow.add_edge("prepare_ticket", END)
    workflow.add_edge("create_ticket_mcp", END)

    checkpointer = MemorySaver() if memory_saver else None
    compiled = workflow.compile(checkpointer=checkpointer)
    return MaintiDocAgentGraph(compiled)

class MaintiDocAgentGraph:
    def __init__(self, compiled_graph):
        self._compiled = compiled_graph

    def invoke(self, state, config=None, **kwargs):
        if config is None:
            config = {"configurable": {"thread_id": f"thread_{uuid.uuid4().hex}"}}
        elif "configurable" not in config:
            config["configurable"] = {"thread_id": f"thread_{uuid.uuid4().hex}"}
        elif "thread_id" not in config["configurable"]:
            config["configurable"]["thread_id"] = f"thread_{uuid.uuid4().hex}"
        return self._compiled.invoke(state, config=config, **kwargs)

    def stream(self, state, config=None, **kwargs):
        if config is None:
            config = {"configurable": {"thread_id": f"thread_{uuid.uuid4().hex}"}}
        elif "configurable" not in config:
            config["configurable"] = {"thread_id": f"thread_{uuid.uuid4().hex}"}
        elif "thread_id" not in config["configurable"]:
            config["configurable"]["thread_id"] = f"thread_{uuid.uuid4().hex}"
        return self._compiled.stream(state, config=config, **kwargs)

    def __getattr__(self, name):
        return getattr(self._compiled, name)

agent_graph = build_maintidoc_graph()
