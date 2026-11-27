"""Index texte BGE-M3, index image CLIP et fusion RRF."""
from __future__ import annotations

import json
import io
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image as PILImage
from sentence_transformers import SentenceTransformer

from .config import (
    IMAGE_DIR,
    IMAGE_EMBEDDING_MODEL,
    IMAGE_TOP_K,
    INDEX_DIR,
    MAX_CONTEXT_CHARS,
    MAX_IMAGES,
    RRF_K,
    ROOT,
    TEXT_EMBEDDING_MODEL,
    TEXT_TOP_K,
    TOP_PAGES,
    USE_RERANKER,
    ensure_dirs,
)
from .rerank import rerank_hits


@lru_cache(maxsize=1)
def text_model() -> SentenceTransformer:
    return SentenceTransformer(TEXT_EMBEDDING_MODEL, device="cpu")


@lru_cache(maxsize=1)
def image_model() -> SentenceTransformer:
    return SentenceTransformer(IMAGE_EMBEDDING_MODEL, device="cpu")


class TextIndex:
    """Index vectoriel des passages texte et tableaux."""

    def __init__(self, chunks: list[dict], embeddings: np.ndarray):
        self.chunks = chunks
        self.embeddings = embeddings.astype(np.float32)

    @classmethod
    def build(cls, chunks: list[dict]) -> "TextIndex":
        ensure_dirs()
        model = text_model()
        vectors = model.encode(
            [c["text"] for c in chunks],
            normalize_embeddings=True,
            show_progress_bar=True,
            batch_size=16,
        )
        vectors = np.asarray(vectors, dtype=np.float32)
        np.save(INDEX_DIR / "text_embeddings.npy", vectors)
        (INDEX_DIR / "text_chunks.json").write_text(
            json.dumps(chunks, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return cls(chunks, vectors)

    @classmethod
    def load(cls) -> "TextIndex":
        chunks = json.loads((INDEX_DIR / "text_chunks.json").read_text(encoding="utf-8"))
        vectors = np.load(INDEX_DIR / "text_embeddings.npy")
        return cls(chunks, vectors)

    def search(self, query: str, top_k: int = TEXT_TOP_K) -> list[dict]:
        q = text_model().encode([query], normalize_embeddings=True)[0]
        scores = self.embeddings @ np.asarray(q, dtype=np.float32)
        order = np.argsort(-scores)[:top_k]
        hits = []
        for rank, idx in enumerate(order, 1):
            chunk = self.chunks[int(idx)]
            hits.append({
                "rank": rank,
                "score": float(scores[idx]),
                "chunk_id": chunk["chunk_id"],
                "element_id": chunk["source_element_id"],
                "page": chunk["page"],
                "type": chunk["type"],
                "text": chunk["text"],
            })
        return hits


class ImageIndex:
    """Index vectoriel CLIP des schémas (couverture exclue)."""

    def __init__(self, images: list[dict], embeddings: np.ndarray):
        self.images = images
        self.embeddings = embeddings.astype(np.float32)

    @classmethod
    def build(cls, images: list[dict]) -> "ImageIndex":
        ensure_dirs()
        images = [im for im in images if im["kind"] == "figure"]

        pil_images = []
        for im in images:
            with PILImage.open(ROOT / im["path"]) as picture:
                pil_images.append(picture.convert("RGB").copy())

        vectors = image_model().encode(
            pil_images, normalize_embeddings=True, show_progress_bar=True
        )
        vectors = np.asarray(vectors, dtype=np.float32)
        np.save(INDEX_DIR / "image_embeddings.npy", vectors)
        (INDEX_DIR / "image_manifest.json").write_text(
            json.dumps(images, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return cls(images, vectors)

    @classmethod
    def load(cls) -> "ImageIndex":
        images = json.loads((INDEX_DIR / "image_manifest.json").read_text(encoding="utf-8"))
        vectors = np.load(INDEX_DIR / "image_embeddings.npy")
        return cls(images, vectors)

    def search(self, query: str, top_k: int = IMAGE_TOP_K) -> list[dict]:
        q = image_model().encode([query], normalize_embeddings=True)[0]
        scores = self.embeddings @ np.asarray(q, dtype=np.float32)
        order = np.argsort(-scores)[:top_k]
        hits = []
        for rank, idx in enumerate(order, 1):
            image = self.images[int(idx)]
            hits.append({
                "rank": rank,
                "score": float(scores[idx]),
                "element_id": image["element_id"],
                "figure_id": image["figure_id"],
                "page": image["page"],
                "type": "image",
                "path": image["path"],
                "filename": image["filename"],
            })
        return hits

    def search_vector(self, image_bytes: bytes, top_k: int = IMAGE_TOP_K) -> list[dict]:
        """Recherche par image utilisateur, sans passer par une requête texte."""
        with PILImage.open(io.BytesIO(image_bytes)) as picture:
            image = picture.convert("RGB")
            vector = image_model().encode([image], normalize_embeddings=True)[0]

        scores = self.embeddings @ np.asarray(vector, dtype=np.float32)
        order = np.argsort(-scores)[:top_k]
        hits = []
        for rank, idx in enumerate(order, 1):
            item = self.images[int(idx)]
            hits.append({
                "rank": rank,
                "score": float(scores[idx]),
                "element_id": item["element_id"],
                "figure_id": item["figure_id"],
                "page": item["page"],
                "type": "image",
                "path": item["path"],
                "filename": item["filename"],
            })
        return hits


def rrf_fuse(text_hits: list[dict], image_hits: list[dict],
             k: int = RRF_K, top_pages: int = TOP_PAGES) -> list[dict]:
    """Fusionne les rangs au niveau des pages (les scores ne sont pas comparables)."""
    totals: dict[int, float] = {}
    contributors: dict[int, set[str]] = {}
    for source, hits in (("texte", text_hits), ("visuel", image_hits)):
        seen_pages: set[int] = set()
        for hit in hits:
            page = int(hit["page"])
            if page in seen_pages:
                continue
            seen_pages.add(page)
            totals[page] = totals.get(page, 0.0) + 1.0 / (k + hit["rank"])
            contributors.setdefault(page, set()).add(source)

    ordered = sorted(totals.items(), key=lambda item: -item[1])[:top_pages]
    return [
        {"page": page, "rrf": score, "sources": sorted(contributors[page])}
        for page, score in ordered
    ]


def build_evidence(text_hits: list[dict], image_hits: list[dict],
                   pages: list[dict], max_chars: int = MAX_CONTEXT_CHARS,
                   max_images: int = MAX_IMAGES) -> tuple[list[dict], list[dict]]:
    """Construit le dossier de preuves borné transmis au modèle."""
    selected_pages = {p["page"] for p in pages}
    evidence: list[dict] = []
    used = 0

    for hit in text_hits:
        if hit["page"] not in selected_pages or used >= max_chars:
            continue
        excerpt = hit["text"][: min(2400, max_chars - used)]
        if not excerpt:
            continue
        evidence.append({
            "id": hit["element_id"],
            "chunk_id": hit["chunk_id"],
            "page": hit["page"],
            "type": hit["type"],
            "content": excerpt,
        })
        used += len(excerpt)

    chosen_images = []
    for page_info in pages:
        if len(chosen_images) >= max_images:
            break
        for hit in image_hits:
            if hit["page"] == page_info["page"]:
                chosen_images.append(hit)
                evidence.append({
                    "id": hit["element_id"],
                    "page": hit["page"],
                    "type": "image",
                    "content": f"Schéma {hit['figure_id']} (page {hit['page']}).",
                })
                break

    return evidence, chosen_images


class Pipeline:
    """Façade utilisée par les notebooks et l'application."""

    def __init__(self, text_index, image_index, qdrant_bundle=None):
        self.text_index = text_index
        self.image_index = image_index
        self._qdrant_bundle = qdrant_bundle

    @classmethod
    def load_or_build(cls, chunks: list[dict] | None = None,
                      images: list[dict] | None = None,
                      backend: str = "numpy") -> "Pipeline":
        if backend == "qdrant":
            try:
                from .vector_store import load_bundle

                bundle = load_bundle()
                return cls(bundle.text, bundle.image, qdrant_bundle=bundle)
            except Exception:
                pass

        try:
            return cls(TextIndex.load(), ImageIndex.load())
        except FileNotFoundError:
            if chunks is None or images is None:
                raise
            return cls(TextIndex.build(chunks), ImageIndex.build(images))

    def search(self, question: str, visual_query: str | None = None,
               rerank: bool = USE_RERANKER, image_bytes: bytes | None = None,
               image_description: str | None = None) -> dict:
        query_text = question
        if image_description:
            query_text = f"{question}\n{image_description}"

        candidate_k = 12 if rerank else TEXT_TOP_K
        text_hits = self.text_index.search(query_text, top_k=max(candidate_k, TEXT_TOP_K))
        if rerank:
            text_hits = rerank_hits(question, text_hits, top_k=TEXT_TOP_K)

        if image_bytes and hasattr(self.image_index, "search_vector"):
            image_hits = self.image_index.search_vector(image_bytes)
        else:
            image_hits = self.image_index.search(visual_query or question)

        pages = rrf_fuse(text_hits, image_hits)
        evidence, images = build_evidence(text_hits, image_hits, pages)
        return {
            "question": question,
            "visual_query": visual_query,
            "image_description": image_description,
            "text_hits": text_hits,
            "image_hits": image_hits,
            "pages": pages,
            "evidence": evidence,
            "images": images,
        }

    def close(self) -> None:
        if self._qdrant_bundle is not None:
            self._qdrant_bundle.close()

