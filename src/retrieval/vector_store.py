"""Vector Store & Qdrant Interface Module.

Stores passage embeddings and visual embeddings with RBAC pre-filtering.
"""

from typing import List, Dict, Any, Optional
import numpy as np
from src.security.access_control import AccessControlService, UserContext

class VectorSearchResult:
    def __init__(self, document: Dict[str, Any], score: float):
        self.document = document
        self.score = score

    def to_dict(self) -> Dict[str, Any]:
        return {
            "document": self.document,
            "score": round(float(self.score), 4)
        }

class QdrantCompatibleVectorStore:
    def __init__(self, dimension: int = 128):
        self.dimension = dimension
        self.documents: List[Dict[str, Any]] = []
        self.text_embeddings: List[np.ndarray] = []
        self.visual_embeddings: List[Optional[np.ndarray]] = []

    def clear(self):
        self.documents = []
        self.text_embeddings = []
        self.visual_embeddings = []

    def add_documents(
        self,
        docs: List[Dict[str, Any]],
        text_vecs: List[np.ndarray],
        visual_vecs: Optional[List[Optional[np.ndarray]]] = None
    ):
        for i, doc in enumerate(docs):
            self.documents.append(doc)
            self.text_embeddings.append(text_vecs[i])
            if visual_vecs and i < len(visual_vecs):
                self.visual_embeddings.append(visual_vecs[i])
            else:
                self.visual_embeddings.append(None)

    def search_text(
        self,
        query_vector: np.ndarray,
        user: UserContext,
        top_k: int = 5
    ) -> List[VectorSearchResult]:
        """Performs text similarity search with strict RBAC pre-filtering."""
        candidates = []
        for idx, doc in enumerate(self.documents):
            # RBAC pre-filtering: check if user has access to document's group
            doc_groups = doc.get("access_groups", [])
            if not AccessControlService.verify_document_access(user, doc_groups):
                continue

            doc_vec = self.text_embeddings[idx]
            # Cosine similarity
            score = float(np.dot(query_vector, doc_vec))
            candidates.append(VectorSearchResult(document=doc, score=score))

        candidates.sort(key=lambda x: x.score, reverse=True)
        return candidates[:top_k]

    def search_visual(
        self,
        query_image_vector: np.ndarray,
        user: UserContext,
        top_k: int = 5
    ) -> List[VectorSearchResult]:
        """Performs visual similarity search with strict RBAC pre-filtering."""
        candidates = []
        for idx, doc in enumerate(self.documents):
            # Check RBAC
            doc_groups = doc.get("access_groups", [])
            if not AccessControlService.verify_document_access(user, doc_groups):
                continue

            doc_img_vec = self.visual_embeddings[idx]
            if doc_img_vec is None:
                continue

            score = float(np.dot(query_image_vector, doc_img_vec))
            candidates.append(VectorSearchResult(document=doc, score=score))

        candidates.sort(key=lambda x: x.score, reverse=True)
        return candidates[:top_k]

vector_store = QdrantCompatibleVectorStore()
