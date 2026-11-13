"""MAINTIDOC Data Models"""

from .schemas import (
    Citation,
    AssistantResponse,
    UserContext,
    QueryRequest,
    TicketDraft,
    TicketApprovalRequest,
    VisualAnalysisResult
)
from .mcp_types import EquipmentHistoryRecord, MaintenanceTicket

__all__ = [
    "Citation",
    "AssistantResponse",
    "UserContext",
    "QueryRequest",
    "TicketDraft",
    "TicketApprovalRequest",
    "VisualAnalysisResult",
    "EquipmentHistoryRecord",
    "MaintenanceTicket",
]
