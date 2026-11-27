"""Stockage vectoriel Qdrant local (mode fichier) pour MaintiDoc.

Qdrant est utilisé en mode local persistant : pas besoin de serveur Docker pour
la démonstration, mais l'API est la même qu'un Qdrant distant.
"""
from __future__ import annotations

import json
import io
from pathlib import Path

import numpy as np
from PIL import Image as PILImage
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from .config import INDEX_DIR, QDRANT_API_KEY, QDRANT_URL, ensure_dirs
from .retrieval import ImageIndex, TextIndex, image_model, text_model

QDRANT_DIR = INDEX_DIR / "qdrant"
TEXT_COLLECTION = "maintidoc_text"
IMAGE_COLLECTION = "maintidoc_images"


class QdrantStore:
    def __init__(self, path: Path = QDRANT_DIR):
        ensure_dirs()
        if QDRANT_URL:
            self.client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
        else:
            self.client = QdrantClient(path=str(path))

    def close(self) -> None:
        self.client.close()


class QdrantTextIndex:
    def __init__(self, client: QdrantClient):
        self.client = client

    def search(self, query: str, top_k: int = 6) -> list[dict]:
        q = text_model().encode([query], normalize_embeddings=True)[0].tolist()
        response = self.client.query_points(
            collection_name=TEXT_COLLECTION, query=q, limit=top_k, with_payload=True
        )
        hits = []
        for rank, point in enumerate(response.points, 1):
            payload = point.payload or {}
            hits.append({
                "rank": rank,
                "score": float(point.score),
                "chunk_id": payload.get("chunk_id"),
                "element_id": payload.get("source_element_id"),
                "page": payload.get("page"),
                "type": payload.get("type"),
                "text": payload.get("text"),
            })
        return hits


class QdrantImageIndex:
    def __init__(self, client: QdrantClient):
        self.client = client

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        q = image_model().encode([query], normalize_embeddings=True)[0].tolist()
        response = self.client.query_points(
            collection_name=IMAGE_COLLECTION, query=q, limit=top_k, with_payload=True
        )
        hits = []
        for rank, point in enumerate(response.points, 1):
            payload = point.payload or {}
            hits.append({
                "rank": rank,
                "score": float(point.score),
                "element_id": payload.get("element_id"),
                "figure_id": payload.get("figure_id"),
                "page": payload.get("page"),
                "type": "image",
                "path": payload.get("path"),
                "filename": payload.get("filename"),
            })
        return hits

    def search_vector(self, image_bytes: bytes, top_k: int = 5) -> list[dict]:
        """Recherche par image utilisateur dans la collection Qdrant."""
        with PILImage.open(io.BytesIO(image_bytes)) as picture:
            image = picture.convert("RGB")
            q = image_model().encode([image], normalize_embeddings=True)[0].tolist()

        response = self.client.query_points(
            collection_name=IMAGE_COLLECTION, query=q, limit=top_k, with_payload=True
        )
        hits = []
        for rank, point in enumerate(response.points, 1):
            payload = point.payload or {}
            hits.append({
                "rank": rank,
                "score": float(point.score),
                "element_id": payload.get("element_id"),
                "figure_id": payload.get("figure_id"),
                "page": payload.get("page"),
                "type": "image",
                "path": payload.get("path"),
                "filename": payload.get("filename"),
            })
        return hits


class QdrantBundle:
    """Un seul client Qdrant partagé par les index texte et image."""

    def __init__(self):
        self.store = QdrantStore()
        self.client = self.store.client
        self.text = QdrantTextIndex(self.client)
        self.image = QdrantImageIndex(self.client)

    def available(self) -> bool:
        return (
            self.client.collection_exists(TEXT_COLLECTION)
            and self.client.collection_exists(IMAGE_COLLECTION)
        )

    @classmethod
    def build(cls, text: TextIndex, image: ImageIndex) -> "QdrantBundle":
        bundle = cls()
        client = bundle.client
        for collection, size in (
            (TEXT_COLLECTION, text.embeddings.shape[1]),
            (IMAGE_COLLECTION, image.embeddings.shape[1]),
        ):
            if client.collection_exists(collection):
                client.delete_collection(collection)
            client.create_collection(
                collection_name=collection,
                vectors_config=VectorParams(size=size, distance=Distance.COSINE),
            )

        client.upsert(
            collection_name=TEXT_COLLECTION,
            points=[
                PointStruct(id=i, vector=text.embeddings[i].tolist(), payload=chunk)
                for i, chunk in enumerate(text.chunks)
            ],
        )
        client.upsert(
            collection_name=IMAGE_COLLECTION,
            points=[
                PointStruct(id=i, vector=image.embeddings[i].tolist(), payload=img)
                for i, img in enumerate(image.images)
            ],
        )
        return bundle

    def close(self) -> None:
        self.store.close()


def build_from_local_indexes() -> dict:
    text = TextIndex.load()
    image = ImageIndex.load()
    bundle = QdrantBundle.build(text, image)
    result = {
        "text_collection": TEXT_COLLECTION,
        "image_collection": IMAGE_COLLECTION,
        "text_points": len(text.chunks),
        "image_points": len(image.images),
    }
    bundle.close()
    return result


def load_bundle() -> QdrantBundle:
    bundle = QdrantBundle()
    if not bundle.available():
        bundle.close()
        raise FileNotFoundError("Collections Qdrant absentes")
    return bundle


if __name__ == "__main__":
    print(json.dumps(build_from_local_indexes(), ensure_ascii=False, indent=2))
