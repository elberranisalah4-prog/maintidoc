"""Unit tests for Multimodal RAG Ingestion & Retrieval."""

import pytest
from src.ingestion.indexer import ingestion_pipeline
from src.retrieval import (
    vector_store,
    embedding_service,
    reciprocal_rank_fusion,
    default_reranker,
    baseline_reranker
)
from src.security.access_control import MOCK_USERS

@pytest.fixture(scope="module", autouse=True)
def init_index():
    ingestion_pipeline.run_ingestion()

def test_vector_search_with_rbac_filtering():
    user_pompes = MOCK_USERS["tech_01"] # Only authorized on pompes
    
    # Query related to compressor
    q_vec = embedding_service.encode_text("filtre séparateur compresseur")
    results = vector_store.search_text(q_vec, user_pompes, top_k=5)
    
    # Must NOT contain any compressor documents
    for res in results:
        doc = res.document
        assert "compresseurs" not in doc.get("access_groups", [])

def test_reciprocal_rank_fusion():
    user = MOCK_USERS["tech_all"]
    q_vec = embedding_service.encode_text("garniture mécanique pompe 45mm")
    text_res = vector_store.search_text(q_vec, user, top_k=5)
    
    fused = reciprocal_rank_fusion([text_res], k=60, top_n=3)
    assert len(fused) > 0
    assert "rrf_score" in fused[0]
    assert fused[0]["document"]["document_id"] == "manuel_pompe_cp200"

def test_reranker_relevance_boost():
    query = "couple de serrage bride 35 Nm"
    passage_good = "Couple de serrage prescrit pour la bride de presse-étoupe : 35 Nm."
    passage_bad = "Le compresseur fonctionne à 7.5 bars de débit d'air."

    score_good = default_reranker.compute_score(query, passage_good)
    score_bad = default_reranker.compute_score(query, passage_bad)
    assert score_good > score_bad
