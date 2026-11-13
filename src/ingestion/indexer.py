"""Ingestion & Indexing Pipeline Module.

Indexes all PDFs and diagrams from the corpus into the multimodal vector store.
"""

from pathlib import Path
from config import CORPUS_DIR
from src.ingestion.pdf_processor import PDFProcessor
from src.retrieval.embeddings import embedding_service
from src.retrieval.vector_store import vector_store

class IngestionPipeline:
    @staticmethod
    def run_ingestion(corpus_dir: Path = CORPUS_DIR) -> int:
        """Processes all PDF files in corpus_dir and populates the vector store."""
        pdf_files = list(corpus_dir.glob("*.pdf"))
        all_chunks = []

        for pdf_path in pdf_files:
            chunks = PDFProcessor.process_pdf(pdf_path)
            all_chunks.extend(chunks)

        if not all_chunks:
            return 0

        # Convert chunks to dicts
        doc_dicts = [c.to_dict() for c in all_chunks]
        texts = [c.text_content for c in all_chunks]
        
        # Generate text embeddings
        text_vecs = embedding_service.encode_texts(texts)

        # Generate visual embeddings for chunks that have an associated image
        visual_vecs = []
        for c in all_chunks:
            if c.image_path and Path(c.image_path).exists():
                v_vec = embedding_service.encode_image(c.image_path)
                visual_vecs.append(v_vec)
            else:
                visual_vecs.append(None)

        vector_store.clear()
        vector_store.add_documents(doc_dicts, text_vecs, visual_vecs)
        return len(all_chunks)

ingestion_pipeline = IngestionPipeline()
