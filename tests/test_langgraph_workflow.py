"""Unit tests for LangGraph Agentic Workflow."""

from src.agent.graph import agent_graph
from config import IMAGES_DIR

def test_workflow_nominal_pump_query():
    state = {
        "user_id": "tech_01",
        "query": "Quel est le couple de serrage pour la bride de pompe CP-200 ?",
        "equipment_id": "PUMP-CP200-A"
    }
    res = agent_graph.invoke(state)
    assert res["status"] == "answered"
    assert "35 Nm" in res["answer"]
    assert len(res["citations"]) > 0
    assert res["citations"][0]["document_id"] == "manuel_pompe_cp200"

def test_workflow_multimodal_image_alarm():
    img_path = str(IMAGES_DIR / "panel_cv50_orange_alarm.jpg")
    state = {
        "user_id": "tech_all",
        "query": "Que signifie ce voyant orange ?",
        "image_path": img_path,
        "equipment_id": "COMP-CV50-01"
    }
    res = agent_graph.invoke(state)
    assert res["status"] == "answered"
    assert "colmatage filtre séparateur" in res["answer"].lower()
    assert len(res["citations"]) > 0

def test_workflow_ambiguous_image_needs_clarification():
    img_path = str(IMAGES_DIR / "blurry_nameplate.jpg")
    state = {
        "user_id": "tech_01",
        "query": "Donne la référence de la pièce sur cet équipement.",
        "image_path": img_path
    }
    res = agent_graph.invoke(state)
    assert res["status"] == "needs_clarification"
    assert len(res["uncertainties"]) > 0
    assert res["clarification_question"] is not None

def test_workflow_ticket_draft_hitl():
    state = {
        "user_id": "tech_all",
        "query": "Prépare un ticket de maintenance pour remplacer la cartouche sur COMP-CV50-01.",
        "equipment_id": "COMP-CV50-01"
    }
    res = agent_graph.invoke(state)
    assert res["status"] == "action_required"
    assert res["ticket_draft"] is not None
    assert "approval_token" in res["ticket_draft"]
