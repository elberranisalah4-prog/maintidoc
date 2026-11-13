"""Pytest configuration and global fixtures."""

import pytest
from src.ingestion.indexer import ingestion_pipeline

@pytest.fixture(scope="session", autouse=True)
def setup_vector_index():
    """Ensures documents are indexed before running any test."""
    ingestion_pipeline.run_ingestion()
