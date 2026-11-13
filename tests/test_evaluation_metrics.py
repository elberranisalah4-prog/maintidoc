"""Unit tests for Evaluation Metrics (nDCG@k, MRR@k)."""

from src.retrieval.reranker import calculate_mrr_at_k, calculate_ndcg_at_k

def test_mrr_first_rank():
    items = [
        {"document": {"document_id": "target_doc"}},
        {"document": {"document_id": "other_doc"}}
    ]
    mrr = calculate_mrr_at_k(items, "target_doc", k=10)
    assert mrr == 1.0

def test_mrr_second_rank():
    items = [
        {"document": {"document_id": "other_doc"}},
        {"document": {"document_id": "target_doc"}}
    ]
    mrr = calculate_mrr_at_k(items, "target_doc", k=10)
    assert mrr == 0.5

def test_ndcg_perfect_ranking():
    items = [
        {"document": {"document_id": "target_doc"}},
        {"document": {"document_id": "other_doc"}}
    ]
    ndcg = calculate_ndcg_at_k(items, "target_doc", k=5)
    assert round(ndcg, 2) == 1.0
