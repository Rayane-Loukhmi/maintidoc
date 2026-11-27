from maintidoc.vector_store import load_bundle


def test_qdrant_searches_text_and_images():
    bundle = load_bundle()
    try:
        text_hits = bundle.text.search("Que signifie AL-01 ?", top_k=5)
        image_hits = bundle.image.search("orange warning LED front panel", top_k=3)
        assert any(hit["page"] == 5 for hit in text_hits)
        assert len(image_hits) == 3
    finally:
        bundle.close()
