"""Pydantic models for structured agent outputs, citations, and user requests."""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field

class Citation(BaseModel):
    document_id: str = Field(description="Identifiant unique du document source")
    page: int = Field(description="Numéro de page exact")
    element_id: str = Field(description="Identifiant d'élément (figure, tableau, paragraphe)")

class AssistantResponse(BaseModel):
    status: Literal["answered", "needs_clarification", "action_required"] = Field(
        default="answered",
        description="Statut opérationnel de la réponse"
    )
    answer: str = Field(description="Réponse textuelle claire et étayée")
    citations: List[Citation] = Field(
        default_factory=list,
        description="Liste des citations étayant les affirmations"
    )
    uncertainties: List[str] = Field(
        default_factory=list,
        description="Points de doute ou informations manquantes"
    )
    clarification_question: Optional[str] = Field(
        default=None,
        description="Question posée au technicien si le statut est needs_clarification"
    )
    proposed_action: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Action sensible proposée nécessitant validation humaine (ex: brouillon de ticket)"
    )

class VisualIndicator(BaseModel):
    name: str
    color: str
    state: Literal["on", "off", "blinking", "unclear"]

class VisualAnalysisResult(BaseModel):
    equipment_detected: Optional[str] = None
    indicators: List[VisualIndicator] = Field(default_factory=list)
    is_readable: bool = True
    visual_anomalies: List[str] = Field(default_factory=list)
    uncertainties: List[str] = Field(default_factory=list)

class UserContext(BaseModel):
    user_id: str
    username: str
    role: Literal["technicien", "responsable", "auditeur"]
    authorized_groups: List[str] = Field(default_factory=lambda: ["pompes", "compresseurs"])

class QueryRequest(BaseModel):
    query: str
    image_base64: Optional[str] = None
    image_path: Optional[str] = None
    equipment_id: Optional[str] = None
    user_id: str = "tech_01"
    conversation_id: Optional[str] = None

class TicketDraft(BaseModel):
    ticket_id: str
    equipment_id: str
    title: str
    description: str
    priority: Literal["low", "medium", "high", "urgent"] = "medium"
    citations: List[Citation] = Field(default_factory=list)
    suggested_parts: List[str] = Field(default_factory=list)
    approval_token: str
    idempotency_key: str

class TicketApprovalRequest(BaseModel):
    ticket_id: str
    user_id: str
    action: Literal["approve", "reject", "modify"]
    approval_token: str
    modified_title: Optional[str] = None
    modified_description: Optional[str] = None
