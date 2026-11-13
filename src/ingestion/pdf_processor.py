"""PDF & Multimodal Document Processing Module.

Splits technical PDFs and diagrams into indexed chunks preserving:
- document_id, version, page, element_id, equipment_type, access_groups.
"""

from pathlib import Path
from typing import List, Dict, Any
from pypdf import PdfReader
from config import CORPUS_DIR, IMAGES_DIR

class DocumentChunk:
    def __init__(
        self,
        document_id: str,
        version: str,
        page: int,
        element_id: str,
        equipment_type: str,
        access_groups: List[str],
        content_type: str,
        text_content: str,
        image_path: str = None
    ):
        self.document_id = document_id
        self.version = version
        self.page = page
        self.element_id = element_id
        self.equipment_type = equipment_type
        self.access_groups = access_groups
        self.content_type = content_type
        self.text_content = text_content
        self.image_path = image_path

    def to_dict(self) -> Dict[str, Any]:
        return {
            "document_id": self.document_id,
            "version": self.version,
            "page": self.page,
            "element_id": self.element_id,
            "equipment_type": self.equipment_type,
            "access_groups": self.access_groups,
            "content_type": self.content_type,
            "text_content": self.text_content,
            "image_path": self.image_path
        }

class PDFProcessor:
    @staticmethod
    def process_pdf(pdf_path: Path) -> List[DocumentChunk]:
        """Extracts text and elements from a technical maintenance PDF."""
        chunks: List[DocumentChunk] = []
        reader = PdfReader(str(pdf_path))
        doc_filename = pdf_path.stem

        # Metadata mapping based on document naming
        if "pompe" in doc_filename.lower():
            doc_id = "manuel_pompe_cp200"
            version = "2.4"
            eq_type = "Pompe Centrifuge CP-200"
            access_groups = ["pompes"]
        elif "compresseur" in doc_filename.lower():
            doc_id = "manuel_compresseur_cv50"
            version = "3.1"
            eq_type = "Compresseur Rotatif CV-50"
            access_groups = ["compresseurs"]
        else:
            doc_id = doc_filename
            version = "1.0"
            eq_type = "Général"
            access_groups = ["general"]

        for page_idx, page in enumerate(reader.pages):
            page_num = page_idx + 1
            raw_text = page.extract_text() or ""
            lines = [line.strip() for line in raw_text.split("\n") if line.strip()]
            
            # Segment into paragraphs & identified elements
            current_element = f"page_{page_num}_intro"
            current_block = []

            for line in lines:
                if "figure" in line.lower() or "tableau" in line.lower() or "section" in line.lower():
                    if current_block:
                        chunks.append(DocumentChunk(
                            document_id=doc_id,
                            version=version,
                            page=page_num,
                            element_id=current_element,
                            equipment_type=eq_type,
                            access_groups=access_groups,
                            content_type="text",
                            text_content=" ".join(current_block)
                        ))
                        current_block = []
                    # Derive element_id
                    tokens = line.lower().replace(":", "").replace(".", "_").split()
                    for t in tokens:
                        if "figure" in t or "tableau" in t or "section" in t:
                            current_element = t
                            break
                    current_block.append(line)
                else:
                    current_block.append(line)

            if current_block:
                chunks.append(DocumentChunk(
                    document_id=doc_id,
                    version=version,
                    page=page_num,
                    element_id=current_element,
                    equipment_type=eq_type,
                    access_groups=access_groups,
                    content_type="text",
                    text_content=" ".join(current_block)
                ))

        # Add visual schematics linked to pages
        if doc_id == "manuel_pompe_cp200":
            fig_path = IMAGES_DIR / "figure_18_2_garniture_cp200.jpg"
            if fig_path.exists():
                chunks.append(DocumentChunk(
                    document_id=doc_id,
                    version=version,
                    page=18,
                    element_id="figure_18_2",
                    equipment_type=eq_type,
                    access_groups=access_groups,
                    content_type="figure",
                    text_content="Figure 18.2 : Coupe transversale garniture mécanique pompe CP-200 arbre 45mm, grain SIC, couple 35 Nm.",
                    image_path=str(fig_path)
                ))
        elif doc_id == "manuel_compresseur_cv50":
            panel_path = IMAGES_DIR / "panel_cv50_orange_alarm.jpg"
            if panel_path.exists():
                chunks.append(DocumentChunk(
                    document_id=doc_id,
                    version=version,
                    page=1,
                    element_id="tableau_alarmes_p1",
                    equipment_type=eq_type,
                    access_groups=access_groups,
                    content_type="figure",
                    text_content="Panneau de commande CV-50 voyants: VERT fixe (en service), ORANGE fixe (alarme colmatage filtre séparateur Delta-P > 0.8 bar), ROUGE (défaut surchauffe).",
                    image_path=str(panel_path)
                ))

        return chunks
