"""Unit tests for Maintenance MCP Server."""

import pytest
from src.mcp_server.server import mcp_server

def test_get_equipment_history_authorized():
    res = mcp_server.get_equipment_history("PUMP-CP200-A", user_id="tech_01")
    assert res.success is True
    assert len(res.data) > 0
    assert "garniture" in res.data[0]["action_taken"].lower()

def test_get_equipment_history_unauthorized():
    # tech_01 is only authorized on pompes, not compresseurs
    res = mcp_server.get_equipment_history("COMP-CV50-01", user_id="tech_01")
    assert res.success is False
    assert "Accès refusé" in res.error

def test_create_ticket_with_valid_token_and_idempotency():
    draft = mcp_server.prepare_ticket_draft(
        equipment_id="COMP-CV50-01",
        title="Test Remplacement Filtre",
        description="Remplacement filtre suite alarme DP",
        user_id="tech_all"
    )
    assert draft["approval_token"] is not None
    assert draft["idempotency_key"] is not None

    # First creation: should succeed
    res1 = mcp_server.create_ticket(
        equipment_id=draft["equipment_id"],
        title=draft["title"],
        description=draft["description"],
        approval_token=draft["approval_token"],
        idempotency_key=draft["idempotency_key"],
        user_id="tech_all"
    )
    assert res1.success is True
    assert "créé avec succès" in res1.data["message"]

    # Duplicate call with same idempotency key: should not re-create
    res2 = mcp_server.create_ticket(
        equipment_id=draft["equipment_id"],
        title=draft["title"],
        description=draft["description"],
        approval_token=draft["approval_token"],
        idempotency_key=draft["idempotency_key"],
        user_id="tech_all"
    )
    assert res2.success is True
    assert "dupliquée évitée" in res2.data["message"]

def test_create_ticket_tampered_token_rejected():
    draft = mcp_server.prepare_ticket_draft(
        equipment_id="PUMP-CP200-A",
        title="Titre Original",
        description="Description originale",
        user_id="tech_01"
    )

    # Attempt to tamper with title using same token
    res = mcp_server.create_ticket(
        equipment_id=draft["equipment_id"],
        title="TITRE MODIFIE SANS ACCORD",
        description=draft["description"],
        approval_token=draft["approval_token"],
        idempotency_key="IDEMP-TAMPER-01",
        user_id="tech_01"
    )
    assert res.success is False
    assert "Jeton d'approbation invalide" in res.error
