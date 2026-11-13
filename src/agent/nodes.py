"""LangGraph Workflow Nodes for MAINTIDOC.

Implements all processing steps:
1. Verify access & check prompt injection
2. Analyze query & image (VLM)
3. Search sources (multimodal RAG + Reranking)
4. Consult maintenance history (MCP)
5. Construct and verify sourced answer
6. Draft ticket & request human validation (HITL)
7. Create ticket via MCP upon explicit approval
"""

from pathlib import Path
from src.agent.state import AgentState
from src.security.access_control import AccessControlService
from src.security.injection_guard import PromptInjectionGuard
from src.security.budgets import RequestBudgetTracker
from src.retrieval import (
    vector_store,
    embedding_service,
    reciprocal_rank_fusion,
    default_reranker
)
from src.mcp_server.server import mcp_server
from src.agent.vlm_client import vlm_client
from src.models.schemas import VisualAnalysisResult

def verify_access_node(state: AgentState) -> AgentState:
    """Node 1: Checks user authorization, RBAC permissions, and prompt injections."""
    user_id = state.get("user_id", "tech_01")
    query = state.get("query", "")
    equipment_id = state.get("equipment_id", "")
    
    # 1. Prompt Injection check
    is_safe, reasons = PromptInjectionGuard.inspect_text(query)
    if not is_safe:
        return {
            **state,
            "injection_detected": True,
            "status": "injection_detected",
            "security_error_message": f"Tentative d'injection de prompt neutralisée : {', '.join(reasons)}",
            "answer": "Sécurité : Requête rejetée suite à la détection de motifs d'injection de prompt ou d'instructions non autorisées."
        }

    # 2. User identification
    user = AccessControlService.get_user(user_id)
    if not user:
        return {
            **state,
            "auth_verified": False,
            "rbac_allowed": False,
            "status": "access_denied",
            "security_error_message": f"Utilisateur inconnu : {user_id}",
            "answer": "Accès refusé : Identifiant utilisateur invalide."
        }

    # 3. RBAC on target equipment family
    if equipment_id:
        eq_upper = equipment_id.upper()
        if ("CV50" in eq_upper or "COMP" in eq_upper) and "compresseurs" not in user.authorized_groups:
            return {
                **state,
                "auth_verified": True,
                "rbac_allowed": False,
                "status": "access_denied",
                "security_error_message": f"Droits insuffisants pour accéder à la famille compresseurs",
                "answer": f"Accès refusé : Le technicien {user.username} ne dispose pas des droits d'accès pour les équipements de type 'compresseurs'."
            }
        elif ("CP200" in eq_upper or "POMPE" in eq_upper) and "pompes" not in user.authorized_groups:
            return {
                **state,
                "auth_verified": True,
                "rbac_allowed": False,
                "status": "access_denied",
                "security_error_message": f"Droits insuffisants pour accéder à la famille pompes",
                "answer": f"Accès refusé : Le technicien {user.username} ne dispose pas des droits d'accès pour les équipements de type 'pompes'."
            }

    return {
        **state,
        "auth_verified": True,
        "rbac_allowed": True,
        "injection_detected": False
    }

def analyze_image_node(state: AgentState) -> AgentState:
    """Node 2: Visual analysis using VLM if photo is provided."""
    image_path = state.get("image_path")
    query = state.get("query", "")
    
    if not image_path or not Path(image_path).exists():
        return {**state, "visual_analysis": None}

    visual_result = vlm_client.analyze_image(image_path, query)
    
    # Auto-detect equipment from image if not already specified
    detected_eq = state.get("equipment_id")
    if not detected_eq and visual_result.equipment_detected:
        if "CV50" in visual_result.equipment_detected:
            detected_eq = "COMP-CV50-01"
        elif "CP200" in visual_result.equipment_detected:
            detected_eq = "PUMP-CP200-A"

    return {
        **state,
        "visual_analysis": visual_result.model_dump(),
        "equipment_id": detected_eq
    }

def search_sources_node(state: AgentState) -> AgentState:
    """Node 3: Multimodal RAG with RRF and adapted cross-encoder reranking."""
    user = AccessControlService.get_user(state.get("user_id", "tech_01"))
    query = state.get("query", "")
    image_path = state.get("image_path")
    
    # Text search
    query_vec = embedding_service.encode_text(query)
    text_results = vector_store.search_text(query_vec, user, top_k=5)
    
    ranked_lists = [text_results]
    
    # Visual search if image is provided
    if image_path and Path(image_path).exists():
        img_vec = embedding_service.encode_image(image_path)
        visual_results = vector_store.search_visual(img_vec, user, top_k=5)
        if visual_results:
            ranked_lists.append(visual_results)

    # Reciprocal Rank Fusion
    fused_candidates = reciprocal_rank_fusion(ranked_lists, k=60, top_n=6)
    
    # Reranking adapted to maintenance vocabulary
    reranked = default_reranker.rerank(query, fused_candidates, top_k=3)

    return {
        **state,
        "retrieved_candidates": fused_candidates,
        "reranked_docs": reranked
    }

def consult_mcp_node(state: AgentState) -> AgentState:
    """Node 4: Queries MCP server for equipment maintenance history."""
    query = state.get("query", "").lower()
    equipment_id = state.get("equipment_id")
    user_id = state.get("user_id", "tech_01")
    
    mcp_history = None
    mcp_tickets = None
    
    # Check if query requests maintenance history or open tickets
    triggers = ["historique", "interventions", "dernière intervention", "ticket", "déjà eu"]
    if any(t in query for t in triggers) and equipment_id:
        hist_resp = mcp_server.get_equipment_history(equipment_id, user_id=user_id)
        if hist_resp.success:
            mcp_history = hist_resp.data
        
        tck_resp = mcp_server.get_open_tickets(equipment_id, user_id=user_id)
        if tck_resp.success:
            mcp_tickets = tck_resp.data

    return {
        **state,
        "mcp_history": mcp_history,
        "mcp_open_tickets": mcp_tickets
    }

def synthesize_response_node(state: AgentState) -> AgentState:
    """Node 5: Builds sourced response with verifiable citations and uncertainty management."""
    query = state.get("query", "")
    reranked_docs = state.get("reranked_docs", [])
    raw_visual = state.get("visual_analysis")
    visual_analysis = VisualAnalysisResult(**raw_visual) if raw_visual else None
    
    mcp_context = {
        "history": state.get("mcp_history"),
        "open_tickets": state.get("mcp_open_tickets")
    }

    # Call VLM synthesis
    res = vlm_client.synthesize_response(query, reranked_docs, visual_analysis, mcp_context)

    # Check if user requested ticket creation
    q_lower = query.lower()
    needs_ticket = "prépare un ticket" in q_lower or "créer un ticket" in q_lower or "prépare un ticket si nécessaire" in q_lower

    return {
        **state,
        "status": res.status,
        "answer": res.answer,
        "citations": [c.model_dump() if hasattr(c, "model_dump") else c for c in res.citations],
        "uncertainties": res.uncertainties,
        "clarification_question": res.clarification_question,
        "needs_ticket": needs_ticket
    }

def prepare_ticket_node(state: AgentState) -> AgentState:
    """Node 6: Prepares ticket draft and requests explicit human approval."""
    equipment_id = state.get("equipment_id", "EQUIP-GENERIC")
    user_id = state.get("user_id", "tech_01")
    answer = state.get("answer", "")
    
    title = f"Intervention corrective sur {equipment_id}"
    if "pompe" in equipment_id.lower() or "cp200" in equipment_id.lower():
        title = "Remplacement garniture mécanique Pompe CP-200"
    elif "cv50" in equipment_id.lower() or "comp" in equipment_id.lower():
        title = "Remplacement cartouche filtre séparateur CV-50"

    description = f"Constaté par technicien : {state.get('query')}\nPrescription documentaire : {answer}"

    draft = mcp_server.prepare_ticket_draft(
        equipment_id=equipment_id,
        title=title,
        description=description,
        user_id=user_id,
        priority="high" if "alarme" in answer.lower() else "medium"
    )

    return {
        **state,
        "status": "action_required",
        "ticket_draft": draft,
        "approval_token": draft["approval_token"],
        "answer": f"{answer}\n\n[ACTION SENSIBLE EN ATTENTE] Un brouillon de ticket a été préparé pour validation humaine obligatoire."
    }

def create_ticket_mcp_node(state: AgentState) -> AgentState:
    """Node 7: Executes ticket creation via MCP only after human approval."""
    draft = state.get("ticket_draft")
    token = state.get("approval_token")
    user_id = state.get("user_id", "tech_01")
    
    if not draft or not token:
        return {
            **state,
            "status": "error",
            "answer": "Échec création ticket : Données ou jeton d'approbation manquants."
        }

    resp = mcp_server.create_ticket(
        equipment_id=draft["equipment_id"],
        title=draft["title"],
        description=draft["description"],
        approval_token=token,
        idempotency_key=draft["idempotency_key"],
        user_id=user_id,
        priority=draft.get("priority", "medium")
    )

    if resp.success:
        ticket_data = resp.data.get("ticket", {})
        return {
            **state,
            "status": "ticket_created",
            "final_ticket_result": resp.data,
            "answer": f"Ticket {ticket_data.get('ticket_id')} créé avec succès sur le serveur MCP suite à votre approbation humaine."
        }
    else:
        return {
            **state,
            "status": "error",
            "answer": f"Création du ticket refusée par le serveur MCP : {resp.error}"
        }
