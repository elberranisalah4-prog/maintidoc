"""Maintenance MCP Server implementation.

Exposes MCP tools according to section 6:
- get_equipment_history(equipment_id)
- get_open_tickets(equipment_id)
- create_ticket(equipment_id, title, description, approval_token)

Features:
- Permission checks on every call
- Human approval token cryptographic verification
- Idempotency protection against duplicate submissions
"""

import uuid
from typing import Dict, Any, Optional
from src.mcp_server.db import mcp_db
from src.models.mcp_types import MCPToolResponse, MaintenanceTicket
from src.security.access_control import AccessControlService

class MaintenanceMCPServer:
    def __init__(self):
        self.db = mcp_db

    def check_auth(self, user_id: str, required_equipment: str) -> bool:
        user = AccessControlService.get_user(user_id)
        if not user:
            return False
        # Map equipment families to group
        eq_upper = required_equipment.upper()
        if "CP200" in eq_upper or "POMPE" in eq_upper:
            target_group = "pompes"
        elif "CV50" in eq_upper or "COMP" in eq_upper:
            target_group = "compresseurs"
        else:
            target_group = "general"
        
        return target_group in user.authorized_groups or "nucleaire_sensible" in user.authorized_groups

    def get_equipment_history(self, equipment_id: str, user_id: str = "tech_01") -> MCPToolResponse:
        """Retrieves past maintenance operations for a given equipment."""
        if not self.check_auth(user_id, equipment_id):
            return MCPToolResponse(
                tool_name="get_equipment_history",
                success=False,
                error=f"Accès refusé pour l'utilisateur '{user_id}' sur l'équipement '{equipment_id}'"
            )

        records = self.db.get_history(equipment_id)
        return MCPToolResponse(
            tool_name="get_equipment_history",
            success=True,
            data=[r.model_dump() for r in records]
        )

    def get_open_tickets(self, equipment_id: str, user_id: str = "tech_01") -> MCPToolResponse:
        """Retrieves currently open tickets for a given equipment."""
        if not self.check_auth(user_id, equipment_id):
            return MCPToolResponse(
                tool_name="get_open_tickets",
                success=False,
                error=f"Accès refusé pour l'utilisateur '{user_id}' sur l'équipement '{equipment_id}'"
            )

        tickets = self.db.get_open_tickets(equipment_id)
        return MCPToolResponse(
            tool_name="get_open_tickets",
            success=True,
            data=[t.model_dump() for t in tickets]
        )

    def prepare_ticket_draft(
        self,
        equipment_id: str,
        title: str,
        description: str,
        user_id: str = "tech_01",
        priority: str = "medium"
    ) -> Dict[str, Any]:
        """Prepares a ticket draft and issues a cryptographic approval token."""
        ticket_id = f"TCK-{uuid.uuid4().hex[:6].upper()}"
        idempotency_key = f"IDEMP-{uuid.uuid4().hex[:8]}"
        approval_token = self.db.generate_approval_token(
            user_id=user_id,
            equipment_id=equipment_id,
            title=title,
            description=description
        )

        return {
            "ticket_id": ticket_id,
            "equipment_id": equipment_id,
            "title": title,
            "description": description,
            "priority": priority,
            "approval_token": approval_token,
            "idempotency_key": idempotency_key,
            "requires_human_validation": True
        }

    def create_ticket(
        self,
        equipment_id: str,
        title: str,
        description: str,
        approval_token: str,
        idempotency_key: str,
        user_id: str = "tech_01",
        priority: str = "medium"
    ) -> MCPToolResponse:
        """Creates a ticket only after explicit human approval token check and idempotency validation."""
        if not self.check_auth(user_id, equipment_id):
            return MCPToolResponse(
                tool_name="create_ticket",
                success=False,
                error=f"Accès refusé pour l'utilisateur '{user_id}'"
            )

        # 1. Idempotency check
        if idempotency_key in self.db.idempotency_keys:
            existing = self.db.idempotency_keys[idempotency_key]
            return MCPToolResponse(
                tool_name="create_ticket",
                success=True,
                data={
                    "ticket": existing.model_dump(),
                    "message": "Ticket déjà créé (clé d'idempotence valide, création dupliquée évitée)"
                }
            )

        # 2. Strict Approval Token verification
        if not self.db.verify_token(approval_token, user_id, equipment_id, title, description):
            return MCPToolResponse(
                tool_name="create_ticket",
                success=False,
                error="Action sensible rejetée : Jeton d'approbation invalide, expiré ou modifié."
            )

        # 3. Create ticket
        new_ticket = MaintenanceTicket(
            ticket_id=f"TCK-{uuid.uuid4().hex[:6].upper()}",
            equipment_id=equipment_id,
            title=title,
            description=description,
            priority=priority,
            status="open",
            created_by=user_id,
            approved_by=user_id,
            idempotency_key=idempotency_key
        )
        saved = self.db.record_ticket(new_ticket, approval_token)

        return MCPToolResponse(
            tool_name="create_ticket",
            success=True,
            data={
                "ticket": saved.model_dump(),
                "message": "Ticket de maintenance créé avec succès après validation humaine."
            }
        )

# Global MCP server instance
mcp_server = MaintenanceMCPServer()
