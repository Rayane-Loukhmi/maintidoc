"""Ingestion du manuel SAN : texte, tableaux et images.

Le point important est l'extraction des tableaux : ``table.extract()`` de
PyMuPDF perd parfois les espaces dans les cellules. On reconstruit donc chaque
cellule avec ``page.get_textbox(Rect(cell))``.
"""
from __future__ import annotations

import hashlib
import io
import json
import re
from pathlib import Path

import pymupdf
from PIL import Image

from .config import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    DOCUMENT_ID,
    DOCUMENT_REVISION,
    IMAGE_DIR,
    PDF_PATH,
    PROCESSED_DIR,
    ensure_dirs,
)


def _clean(text: str) -> str:
    """Normalise les espaces et retire les artefacts de fin de ligne."""
    text = " ".join(text.split())
    text = re.sub(r"\s+([,;:.])", r"\1", text)
    return text.strip()


def _table_rows(page: pymupdf.Page, table) -> list[list[str]]:
    """Extrait les cellules via leur rectangle, pour conserver les espaces."""
    rows: list[list[str]] = []
    for row in table.rows:
        cells: list[str] = []
        for cell in row.cells:
            if cell is None:
                cells.append("")
                continue
            rect = pymupdf.Rect(cell)
            cells.append(_clean(page.get_textbox(rect)))
        if any(cells):
            rows.append(cells)
    return rows


def _rows_to_markdown(rows: list[list[str]]) -> str:
    if not rows:
        return ""
    width = max(len(r) for r in rows)
    normalized = [r + [""] * (width - len(r)) for r in rows]
    header = normalized[0]
    body = normalized[1:]
    lines = ["| " + " | ".join(header) + " |",
             "|" + "|".join(["---"] * width) + "|"]
    for row in body:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def extract_pdf(pdf_path: Path = PDF_PATH) -> dict:
    """Retourne un dictionnaire complet : textes, tableaux, images, métadonnées."""
    ensure_dirs()
    pdf_bytes = pdf_path.read_bytes()
    digest = hashlib.sha256(pdf_bytes).hexdigest()

    text_records: list[dict] = []
    table_records: list[dict] = []
    image_records: list[dict] = []

    with pymupdf.open(pdf_path) as doc:
        for page in doc:
            page_number = page.number + 1
            text = page.get_text("text").strip()
            text_records.append({
                "document_id": DOCUMENT_ID,
                "revision": DOCUMENT_REVISION,
                "page": page_number,
                "element_id": f"P{page_number:02d}-TEXT",
                "type": "text",
                "text": text,
                "sha256": digest,
            })

            for k, table in enumerate(page.find_tables().tables, 1):
                rows = _table_rows(page, table)
                if not rows:
                    continue
                table_records.append({
                    "document_id": DOCUMENT_ID,
                    "revision": DOCUMENT_REVISION,
                    "page": page_number,
                    "element_id": f"P{page_number:02d}-TAB{k:02d}",
                    "type": "table",
                    "rows": rows,
                    "text": _rows_to_markdown(rows),
                    "sha256": digest,
                })

            for j, info in enumerate(page.get_images(full=True), 1):
                xref = info[0]
                payload = doc.extract_image(xref)
                if not payload:
                    continue
                with Image.open(io.BytesIO(payload["image"])) as im:
                    width, height = im.size
                if width < 120 or height < 85:
                    continue

                if page_number == 1:
                    figure_id, kind = "COVER", "cover"
                    name = "cover_page01.png"
                elif 2 <= page_number <= 6:
                    figure_id, kind = f"FIG-{page_number - 1:02d}", "figure"
                    name = f"fig{page_number - 1:02d}_page{page_number:02d}.png"
                else:
                    figure_id, kind = f"P{page_number:02d}-IMG{j:02d}", "illustration"
                    name = f"page{page_number:02d}_image{j:02d}.png"

                path = IMAGE_DIR / name
                path.write_bytes(payload["image"])
                image_records.append({
                    "document_id": DOCUMENT_ID,
                    "revision": DOCUMENT_REVISION,
                    "page": page_number,
                    "element_id": f"P{page_number:02d}-IMG{j:02d}",
                    "figure_id": figure_id,
                    "type": "image",
                    "kind": kind,
                    "path": str(path.relative_to(PROCESSED_DIR.parent.parent)),
                    "filename": name,
                    "width": width,
                    "height": height,
                    "sha256": digest,
                })

    return {
        "document_id": DOCUMENT_ID,
        "revision": DOCUMENT_REVISION,
        "pdf": str(pdf_path),
        "sha256": digest,
        "texts": text_records,
        "tables": table_records,
        "images": image_records,
    }


def _split_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Découpe un texte en fenêtres de mots avec chevauchement."""
    words = text.split()
    if not words:
        return []
    if len(" ".join(words)) <= size:
        return [" ".join(words)]

    chunks: list[str] = []
    start = 0
    while start < len(words):
        current: list[str] = []
        length = 0
        end = start
        while end < len(words):
            word_len = len(words[end]) + (1 if current else 0)
            if length + word_len > size and current:
                break
            current.append(words[end])
            length += word_len
            end += 1
        chunks.append(" ".join(current))
        if end >= len(words):
            break
        # Chevauchement exprimé en mots (approximation de CHUNK_OVERLAP caractères).
        overlap_words = max(1, overlap // 8)
        start = max(start + 1, end - overlap_words)
    return chunks


def build_chunks(document: dict) -> list[dict]:
    """Transforme textes et tableaux en passages indexables."""
    chunks: list[dict] = []

    for record in document["texts"]:
        for k, chunk in enumerate(_split_text(record["text"]), 1):
            chunks.append({
                "chunk_id": f"{record['element_id']}-C{k:02d}",
                "source_element_id": record["element_id"],
                "document_id": record["document_id"],
                "revision": record["revision"],
                "page": record["page"],
                "type": "text",
                "text": chunk,
            })

    for record in document["tables"]:
        chunks.append({
            "chunk_id": f"{record['element_id']}-C01",
            "source_element_id": record["element_id"],
            "document_id": record["document_id"],
            "revision": record["revision"],
            "page": record["page"],
            "type": "table",
            "text": record["text"],
        })

    return chunks


def save_artifacts(document: dict, chunks: list[dict]) -> None:
    ensure_dirs()
    (PROCESSED_DIR / "document.json").write_text(
        json.dumps(document, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (PROCESSED_DIR / "chunks.json").write_text(
        json.dumps(chunks, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (PROCESSED_DIR / "tables.json").write_text(
        json.dumps(document["tables"], ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (PROCESSED_DIR / "texts.json").write_text(
        json.dumps(document["texts"], ensure_ascii=False, indent=2), encoding="utf-8"
    )


def run() -> dict:
    document = extract_pdf()
    chunks = build_chunks(document)
    save_artifacts(document, chunks)
    return {"document": document, "chunks": chunks}


if __name__ == "__main__":
    result = run()
    print(f"Pages : {len(result['document']['texts'])}")
    print(f"Tableaux : {len(result['document']['tables'])}")
    print(f"Images : {len(result['document']['images'])}")
    print(f"Chunks : {len(result['chunks'])}")
    print(f"Artefacts : {PROCESSED_DIR}")
