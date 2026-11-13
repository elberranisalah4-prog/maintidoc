"""FastAPI Application for MAINTIDOC.

Exposes REST endpoints for:
- Technician multimodal queries
- Human-in-the-loop (HITL) ticket approvals
- MCP maintenance queries
- Ingestion management
"""

import base64
import uuid
from pathlib import Path
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import settings, IMAGES_DIR
from src.models.schemas import (
    AssistantResponse,
    QueryRequest,
    TicketApprovalRequest,
    UserContext
)
from src.security.access_control import AccessControlService, MOCK_USERS
from src.agent.graph import agent_graph
from src.mcp_server.server import mcp_server
from src.ingestion.indexer import ingestion_pipeline
from src.retrieval.vector_store import vector_store

app = FastAPI(
    title="MAINTIDOC API",
    description="Assistant documentaire multimodal et agentique pour la maintenance industrielle",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    # Run ingestion of synthetic corpus on startup
    indexed_count = ingestion_pipeline.run_ingestion()
    print(f"[MAINTIDOC Startup] Indexé {indexed_count} segments documentaires dans Qdrant/VectorStore.")

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "MAINTIDOC",
        "version": "1.0.0",
        "indexed_chunks": len(vector_store.documents),
        "mcp_active": True
    }

@app.post("/api/query", response_model=Dict[str, Any])
def submit_query(request: QueryRequest):
    """Processes technician query and optional photo."""
    # Setup initial state
    thread_id = request.conversation_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    image_path = request.image_path
    if request.image_base64:
        # Decode and persist temporary image
        img_data = base64.b64decode(request.image_base64)
        tmp_img = IMAGES_DIR / f"upload_{uuid.uuid4().hex[:8]}.jpg"
        with open(tmp_img, "wb") as f:
            f.write(img_data)
        image_path = str(tmp_img)

    initial_state = {
        "user_id": request.user_id,
        "query": request.query,
        "image_path": image_path,
        "equipment_id": request.equipment_id,
        "citations": [],
        "uncertainties": [],
        "needs_ticket": False
    }

    final_state = agent_graph.invoke(initial_state, config=config)

    return {
        "conversation_id": thread_id,
        "status": final_state.get("status"),
        "answer": final_state.get("answer"),
        "citations": final_state.get("citations", []),
        "uncertainties": final_state.get("uncertainties", []),
        "clarification_question": final_state.get("clarification_question"),
        "ticket_draft": final_state.get("ticket_draft"),
        "visual_analysis": final_state.get("visual_analysis")
    }

@app.post("/api/ticket/approve", response_model=Dict[str, Any])
def approve_ticket(request: TicketApprovalRequest):
    """Human-in-the-loop endpoint: Technicians validate, modify, or reject a proposed ticket."""
    if request.action == "reject":
        return {
            "success": True,
            "message": f"Brouillon de ticket {request.ticket_id} annulé par le technicien."
        }

    # Fetch token and verify
    token_info = mcp_server.db.tokens.get(request.approval_token)
    if not token_info:
        raise HTTPException(status_code=400, detail="Jeton d'approbation inconnu ou expiré.")

    target_title = request.modified_title or token_info["title"]
    target_desc = request.modified_description or token_info["description"]
    
    # If content was modified, a fresh token matching the new content must be re-signed
    if target_title != token_info["title"] or target_desc != token_info["description"]:
        new_token = mcp_server.db.generate_approval_token(
            request.user_id,
            token_info["equipment_id"],
            target_title,
            target_desc
        )
        effective_token = new_token
    else:
        effective_token = request.approval_token

    resp = mcp_server.create_ticket(
        equipment_id=token_info["equipment_id"],
        title=target_title,
        description=target_desc,
        approval_token=effective_token,
        idempotency_key=f"USER_APPR_{uuid.uuid4().hex[:8]}",
        user_id=request.user_id
    )

    if not resp.success:
        raise HTTPException(status_code=403, detail=resp.error)

    return resp.model_dump()

@app.get("/api/mcp/history/{equipment_id}")
def get_equipment_history(equipment_id: str, user_id: str = "tech_01"):
    resp = mcp_server.get_equipment_history(equipment_id, user_id=user_id)
    if not resp.success:
        raise HTTPException(status_code=403, detail=resp.error)
    return resp.model_dump()

@app.get("/api/mcp/tickets/{equipment_id}")
def get_equipment_tickets(equipment_id: str, user_id: str = "tech_01"):
    resp = mcp_server.get_open_tickets(equipment_id, user_id=user_id)
    if not resp.success:
        raise HTTPException(status_code=403, detail=resp.error)
    return resp.model_dump()
