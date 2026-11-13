"""Reciprocal Rank Fusion (RRF) Module.

Combines rankings from textual search and visual search using:
RRF_score(d) = sum_{m in models} [ 1 / (k + rank_m(d)) ]
"""

from typing import List, Dict, Any
from src.retrieval.vector_store import VectorSearchResult

def reciprocal_rank_fusion(
    ranked_lists: List[List[VectorSearchResult]],
    k: int = 60,
    top_n: int = 10
) -> List[Dict[str, Any]]:
    """Merges multiple ranked lists of VectorSearchResult using RRF."""
    doc_scores: Dict[str, float] = {}
    doc_map: Dict[str, Dict[str, Any]] = {}

    for ranked_list in ranked_lists:
        for rank, res in enumerate(ranked_list):
            doc = res.document
            # Unique key for element: doc_id + page + element_id
            doc_key = f"{doc['document_id']}_{doc['page']}_{doc['element_id']}"
            
            if doc_key not in doc_map:
                doc_map[doc_key] = doc
                doc_scores[doc_key] = 0.0

            # RRF formula
            doc_scores[doc_key] += 1.0 / (k + (rank + 1))

    # Sort documents by combined RRF score
    sorted_keys = sorted(doc_scores.keys(), key=lambda x: doc_scores[x], reverse=True)

    fused_results = []
    for key in sorted_keys[:top_n]:
        fused_results.append({
            "document": doc_map[key],
            "rrf_score": round(doc_scores[key], 6)
        })

    return fused_results
