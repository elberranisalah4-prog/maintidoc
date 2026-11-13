"""LangGraph State definition for MAINTIDOC Agent."""

from typing import List, Optional, Dict, Any
from typing_extensions import TypedDict
from src.models.schemas import Citation, VisualAnalysisResult

class AgentState(TypedDict, total=False):
    # User and request metadata
    user_id: str
    query: str
    image_path: Optional[str]
    equipment_id: Optional[str]
    
    # Security and guardrails
    auth_verified: bool
    rbac_allowed: bool
    injection_detected: bool
    security_error_message: Optional[str]
    
    # Multimodal and retrieval data
    visual_analysis: Optional[Dict[str, Any]]
    retrieved_candidates: List[Dict[str, Any]]
    reranked_docs: List[Dict[str, Any]]
    
    # MCP context
    mcp_history: Optional[List[Dict[str, Any]]]
    mcp_open_tickets: Optional[List[Dict[str, Any]]]
    
    # Synthesis & Sourced output
    status: str  # "answered", "needs_clarification", "action_required", "access_denied", "injection_detected"
    answer: str
    citations: List[Dict[str, Any]]
    uncertainties: List[str]
    clarification_question: Optional[str]
    
    # Sensitive Action (HITL)
    needs_ticket: bool
    ticket_draft: Optional[Dict[str, Any]]
    ticket_approved: Optional[bool]
    approval_token: Optional[str]
    final_ticket_result: Optional[Dict[str, Any]]
    
    # Budget tracking
    budget_summary: Dict[str, Any]
