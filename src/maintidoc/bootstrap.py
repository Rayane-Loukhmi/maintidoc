"""Bootstrap Docker : attend Qdrant et construit les collections si nécessaire."""
from __future__ import annotations

import time

from qdrant_client import QdrantClient

from .config import QDRANT_API_KEY, QDRANT_URL
from .retrieval import ImageIndex, TextIndex
from .vector_store import IMAGE_COLLECTION, TEXT_COLLECTION, QdrantBundle


def wait_for_qdrant(timeout: int = 60) -> QdrantClient:
    deadline = time.time() + timeout
    last_error = None
    while time.time() < deadline:
        try:
            client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
            client.get_collections()
            return client
        except Exception as exc:
            last_error = exc
            time.sleep(2)
    raise RuntimeError(f"Qdrant indisponible après {timeout}s : {last_error}")


def main() -> None:
    if not QDRANT_URL:
        print("QDRANT_URL absente : bootstrap ignoré.")
        return

    client = wait_for_qdrant()
    has_text = client.collection_exists(TEXT_COLLECTION)
    has_images = client.collection_exists(IMAGE_COLLECTION)
    client.close()

    if has_text and has_images:
        print("Collections Qdrant déjà présentes.")
        return

    text = TextIndex.load()
    image = ImageIndex.load()
    bundle = QdrantBundle.build(text, image)
    bundle.close()
    print(f"Qdrant initialisé : {len(text.chunks)} passages, {len(image.images)} figures.")


if __name__ == "__main__":
    main()
