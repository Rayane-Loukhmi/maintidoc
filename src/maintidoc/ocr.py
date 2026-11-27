"""OCR local optionnel pour les PDF scannés ou les figures non textuelles.

Le manuel fourni possède une couche texte : l'OCR n'est pas nécessaire pour le
texte principal. Il est fourni pour les corpus scannés et pour les libellés des
schémas.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from .config import PROCESSED_DIR, ROOT


@lru_cache(maxsize=1)
def reader():
    from rapidocr_onnxruntime import RapidOCR

    return RapidOCR()


def ocr_image(path: str | Path) -> str:
    """Retourne le texte détecté dans une image, ou une chaîne vide."""
    result, _ = reader()(str(path))
    if not result:
        return ""
    lines = [item[1] for item in result if len(item) > 1 and item[1]]
    return " ".join(" ".join(lines).split())


def ocr_figures(images: list[dict]) -> list[dict]:
    """Ajoute ``ocr_text`` aux figures, sans modifier les images."""
    output = []
    for image in images:
        if image.get("kind") != "figure":
            output.append(image)
            continue
        path = ROOT / image["path"]
        text = ocr_image(path) if path.is_file() else ""
        output.append({**image, "ocr_text": text})
    return output


if __name__ == "__main__":
    document = json.loads((PROCESSED_DIR / "document.json").read_text(encoding="utf-8"))
    enriched = ocr_figures(document["images"])
    (PROCESSED_DIR / "ocr_figures.json").write_text(
        json.dumps(enriched, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    for image in enriched:
        print(image.get("figure_id"), ":", image.get("ocr_text", "")[:160])
