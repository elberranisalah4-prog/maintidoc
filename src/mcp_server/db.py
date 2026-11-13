"""Database and state storage for the Maintenance MCP Service."""

import hashlib
import hmac
from typing import Dict, List, Optional
from src.models.mcp_types import EquipmentHistoryRecord, MaintenanceTicket
from config import settings

# Pre-populated realistic history for demonstration
SEED_HISTORY: List[EquipmentHistoryRecord] = [
    EquipmentHistoryRecord(
        record_id="HIST-2026-089",
        equipment_id="PUMP-CP200-A",
        date="2026-09-14",
        technician="Alice Martin",
        action_taken="Remplacement préventif garniture mécanique et contrôle alignement",
        symptoms="Légère fuite d'eau au presse-étoupe détectée lors de la ronde",
        parts_replaced=["Garniture mécanique SIC/SIC 45mm", "Joint torique EPDM"]
    ),
    EquipmentHistoryRecord(
        record_id="HIST-2026-042",
        equipment_id="PUMP-CP200-A",
        date="2026-04-10",
        technician="Jean Dupont",
        action_taken="Vidange palier et graissage roulements",
        symptoms="Vibrations anormales mesurées à 4.2 mm/s",
        parts_replaced=["Huile ISO VG 68", "Roulement SKF 6309"]
    ),
    EquipmentHistoryRecord(
        record_id="HIST-2026-104",
        equipment_id="COMP-CV50-01",
        date="2026-10-02",
        technician="Jean Dupont",
        action_taken="Remplacement cartouche séparateur d'huile et réarmement pressostat",
        symptoms="Voyant orange ΔP Filtre allumé fixe, pression différentielle > 0.8 bar",
        parts_replaced=["Cartouche séparateur air/huile ref SP-504", "Joint torique cuve"]
    )
]

SEED_TICKETS: List[MaintenanceTicket] = [
    MaintenanceTicket(
        ticket_id="TCK-1001",
        equipment_id="COMP-CV50-01",
        title="Contrôle périodique vanne thermostatique",
        description="Vérification de la régulation de température huile compresseur après 4000h",
        priority="medium",
        status="open",
        created_at="2026-11-01T08:30:00",
        created_by="tech_01",
        approved_by="manager_01",
        idempotency_key="init_seed_01"
    )
]

class MaintenanceDatabase:
    def __init__(self):
        self.history: List[EquipmentHistoryRecord] = list(SEED_HISTORY)
        self.tickets: List[MaintenanceTicket] = list(SEED_TICKETS)
        self.idempotency_keys: Dict[str, MaintenanceTicket] = {}
        self.tokens: Dict[str, Dict] = {}

    def get_history(self, equipment_id: str) -> List[EquipmentHistoryRecord]:
        return [h for h in self.history if h.equipment_id.upper() == equipment_id.upper()]

    def get_open_tickets(self, equipment_id: str) -> List[MaintenanceTicket]:
        return [t for t in self.tickets if t.equipment_id.upper() == equipment_id.upper() and t.status == "open"]

    def generate_approval_token(self, user_id: str, equipment_id: str, title: str, description: str) -> str:
        """Generates a cryptographic HMAC-SHA256 token tying approval to user and exact content."""
        payload = f"{user_id}:{equipment_id}:{title.strip()}:{description.strip()}"
        token = hmac.new(
            settings.security.jwt_secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        
        self.tokens[token] = {
            "user_id": user_id,
            "equipment_id": equipment_id,
            "title": title.strip(),
            "description": description.strip(),
            "used": False
        }
        return token

    def verify_token(self, token: str, user_id: str, equipment_id: str, title: str, description: str) -> bool:
        """Strict verification: token must match exact content and must not have been already used."""
        token_info = self.tokens.get(token)
        if not token_info:
            return False
        if token_info["used"]:
            return False
        
        expected_payload = f"{user_id}:{equipment_id}:{title.strip()}:{description.strip()}"
        expected_token = hmac.new(
            settings.security.jwt_secret.encode(),
            expected_payload.encode(),
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(token, expected_token)

    def record_ticket(self, ticket: MaintenanceTicket, token: str) -> MaintenanceTicket:
        if token in self.tokens:
            self.tokens[token]["used"] = True
        self.tickets.append(ticket)
        self.idempotency_keys[ticket.idempotency_key] = ticket
        return ticket

mcp_db = MaintenanceDatabase()
