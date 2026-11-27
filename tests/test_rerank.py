from maintidoc.rerank import rerank_hits


def test_reranker_returns_sorted_hits():
    hits = [
        {"text": "Le voyant orange AL-01 indique un chemin FC dégradé.", "rank": 1},
        {"text": "La capacité de stockage est de 88 %.", "rank": 2},
    ]
    result = rerank_hits("Que signifie AL-01 ?", hits, top_k=2)
    assert len(result) == 2
    assert all("rerank_score" in hit for hit in result)
    assert result[0]["rerank_score"] >= result[1]["rerank_score"]
