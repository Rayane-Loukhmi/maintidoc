from maintidoc.config import PDF_PATH
from maintidoc.ingest import extract_pdf


def test_extraction_counts():
    doc = extract_pdf(PDF_PATH)
    assert len(doc["texts"]) == 9
    assert len(doc["tables"]) == 9
    assert len([im for im in doc["images"] if im["kind"] == "figure"]) == 5


def test_table_spaces_are_recovered():
    doc = extract_pdf(PDF_PATH)
    table = next(t for t in doc["tables"] if t["element_id"] == "P02-TAB01")
    assert "Valeur pedagogique" in table["text"]
    assert "SAN-LAB 2000" in table["text"]
