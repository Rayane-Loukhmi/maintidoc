"""Configuration centrale du projet MaintiDoc.

Toutes les chemins sont dérivés de la racine du dépôt afin que les notebooks,
les scripts et l'application Streamlit utilisent les mêmes artefacts.
"""
from __future__ import annotations

import os
from pathlib import Path

# Racine du projet :  src/maintidoc/config.py -> remonter de deux niveaux
ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
IMAGE_DIR = PROCESSED_DIR / "images"
INDEX_DIR = PROCESSED_DIR / "index"
MOCK_DIR = DATA_DIR / "mock"

PDF_PATH = RAW_DIR / "Manuel_Maintenance_SAN_Projet_Integrateur.pdf"
DOCUMENT_ID = "SAN-MAN-001"
DOCUMENT_REVISION = "1.1"

# Modèles
TEXT_EMBEDDING_MODEL = "BAAI/bge-m3"
IMAGE_EMBEDDING_MODEL = "sentence-transformers/clip-ViT-B-32"
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:latest")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")

# Qdrant : vide = mode local fichier ; sinon URL du serveur (Docker)
QDRANT_URL = os.getenv("QDRANT_URL", "").strip()
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "").strip() or None

# Retrieval
TEXT_TOP_K = 6
IMAGE_TOP_K = 5
RRF_K = 60
TOP_PAGES = 4
MAX_CONTEXT_CHARS = 8500
MAX_IMAGES = 1
RERANK_MODEL = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"
USE_RERANKER = False

# Chunking
CHUNK_SIZE = 700
CHUNK_OVERLAP = 120


def ensure_dirs() -> None:
    """Crée les dossiers de travail s'ils n'existent pas."""
    for directory in (PROCESSED_DIR, IMAGE_DIR, INDEX_DIR, MOCK_DIR):
        directory.mkdir(parents=True, exist_ok=True)
