"""Évaluation de la recherche sur un petit jeu de questions de référence."""
from __future__ import annotations

import csv
import json
from pathlib import Path

from maintidoc.config import ROOT
from maintidoc.retrieval import ImageIndex, Pipeline, TextIndex

QUESTIONS = ROOT / "eval" / "questions.jsonl"
RESULTS = ROOT / "eval" / "results.csv"


def _pipeline() -> Pipeline:
    try:
        return Pipeline.load_or_build()
    except FileNotFoundError:
        import json

        chunks = json.loads((ROOT / "data" / "processed" / "chunks.json").read_text(encoding="utf-8"))
        document = json.loads((ROOT / "data" / "processed" / "document.json").read_text(encoding="utf-8"))
        return Pipeline(TextIndex.build(chunks), ImageIndex.build(document["images"]))


def recall(expected: list, found: list) -> float:
    if not expected:
        return 1.0 if not found else 0.0
    return len(set(expected) & set(found)) / len(set(expected))


def main() -> None:
    pipeline = _pipeline()
    questions = [json.loads(line) for line in QUESTIONS.read_text(encoding="utf-8").splitlines() if line.strip()]

    rows = []
    for q in questions:
        result = pipeline.search(q["question"], q.get("visual_query"))
        text_pages = [h["page"] for h in result["text_hits"][:5]]
        rrf_pages = [p["page"] for p in result["pages"]]
        figures = [h["figure_id"] for h in result["image_hits"][:3]]

        expected_pages = q.get("expected_pages", [])
        expected_figures = q.get("expected_figures", [])

        first_rank = None
        for hit in result["text_hits"]:
            if hit["page"] in expected_pages:
                first_rank = hit["rank"]
                break

        rows.append({
            "id": q["id"],
            "question": q["question"],
            "expected_pages": expected_pages,
            "text_pages_top5": text_pages,
            "rrf_pages": rrf_pages,
            "expected_figures": expected_figures,
            "figures_top3": figures,
            "recall_text@5": round(recall(expected_pages, text_pages), 3),
            "recall_rrf": round(recall(expected_pages, rrf_pages), 3),
            "recall_image@3": round(recall(expected_figures, figures), 3),
            "mrr_page": round(1 / first_rank, 3) if first_rank else 0.0,
        })

    RESULTS.parent.mkdir(parents=True, exist_ok=True)
    with RESULTS.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"Questions : {len(rows)}")
    for key in ("recall_text@5", "recall_rrf", "recall_image@3", "mrr_page"):
        print(f"{key}: {sum(r[key] for r in rows) / len(rows):.3f}")
    print(f"Résultats : {RESULTS}")


if __name__ == "__main__":
    main()
