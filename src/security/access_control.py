"""Access Control & RBAC Module.

Enforces document filtering by user permissions before retrieval and during display.
Prevents cross-group leakage.
"""

from typing import List, Dict, Optional
from src.models.schemas import UserContext

# Static registry of mock users and their credentials / groups
MOCK_USERS: Dict[str, UserContext] = {
    "tech_01": UserContext(
        user_id="tech_01",
        username="Jean Dupont (Tech Pompes)",
        role="technicien",
        authorized_groups=["pompes"]
    ),
    "tech_all": UserContext(
        user_id="tech_all",
        username="Alice Martin (Tech Senior)",
        role="technicien",
        authorized_groups=["pompes", "compresseurs"]
    ),
    "manager_01": UserContext(
        user_id="manager_01",
        username="Marc Lefebvre (Responsable)",
        role="responsable",
        authorized_groups=["pompes", "compresseurs", "nucleaire_sensible"]
    ),
    "unauthorized_user": UserContext(
        user_id="unauthorized_user",
        username="Stagiaire Externe",
        role="auditeur",
        authorized_groups=[]
    )
}

class AccessControlService:
    @staticmethod
    def get_user(user_id: str) -> Optional[UserContext]:
        return MOCK_USERS.get(user_id)

    @staticmethod
    def verify_document_access(user: UserContext, document_groups: List[str]) -> bool:
        """Verifies if the user is authorized to read an item belonging to document_groups."""
        if not document_groups:
            return True
        return any(group in user.authorized_groups for group in document_groups)

    @staticmethod
    def filter_documents_for_user(user: UserContext, documents: List[Dict]) -> List[Dict]:
        """Pre-retrieval and post-retrieval filtering based on access groups."""
        return [
            doc for doc in documents
            if AccessControlService.verify_document_access(user, doc.get("access_groups", []))
        ]
