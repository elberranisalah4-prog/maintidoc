"""Pydantic schemas for the Maintenance MCP Service."""

from typing import List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field

class EquipmentHistoryRecord(BaseModel):
    record_id: str
    equipment_id: str
    date: str
    technician: str
    action_taken: str
    symptoms: str
    parts_replaced: List[str] = Field(default_factory=list)

class MaintenanceTicket(BaseModel):
    ticket_id: str
    equipment_id: str
    title: str
    description: str
    priority: str = "medium"
    status: str = "open"  # "open", "in_progress", "closed"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    created_by: str
    approved_by: str
    idempotency_key: str

class MCPToolResponse(BaseModel):
    tool_name: str
    success: bool
    data: Optional[dict | list] = None
    error: Optional[str] = None
