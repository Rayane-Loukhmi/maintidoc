# Ingestion et préparation du corpus

Ce document décrit les fonctions de `src/maintidoc/ingest.py` et `src/maintidoc/ocr.py`.

## 1. Pourquoi cette étape est critique

Un pipeline RAG ne peut pas être meilleur que son extraction. Si le texte, les
tableaux ou les figures sont mal extraits, les embeddings et le modèle reçoivent
des données dégradées.

Le corpus de référence est le manuel **SAN-MAN-001** :

```text
9 pages · 9 tableaux · 6 images (couverture + FIG-01..FIG-05)
```

## 2. `extract_pdf(pdf_path=PDF_PATH) -> dict`

Parcourt le PDF avec PyMuPDF et retourne :

```python
{
    "document_id": "SAN-MAN-001",
    "revision": "1.1",
    "pdf": "...",
    "sha256": "...",
    "texts": [...],
    "tables": [...],
    "images": [...],
}
```

### Textes

Un enregistrement par page :

```python
{
    "document_id": "SAN-MAN-001",
    "revision": "1.1",
    "page": 5,
    "element_id": "P05-TEXT",
    "type": "text",
    "text": "...",
    "sha256": "...",
}
```

Pourquoi `element_id` : il sert de base aux citations (`P05-TEXT`, page 5).

### Tableaux

Chaque tableau possède :

- `element_id` : `P05-TAB01` ;
- `page` ;
- `rows` : liste de lignes ;
- `text` : représentation Markdown.

### Images

Chaque image possède :

- `element_id` : `P05-IMG01` ;
- `figure_id` : `FIG-04` ou `COVER` ;
- `kind` : `figure`, `cover` ou `illustration` ;
- `path`, `filename`, `width`, `height`.

La couverture est marquée `COVER` pour être exclue de l’index visuel.

## 3. `_table_rows(page, table)` : le correctif des espaces

Problème observé :

```python
table.extract()
# ['Valeurpedagogique', 'SAN -LAB 2000']
```

La méthode standard perd les espaces. La fonction reconstruit chaque cellule avec
son rectangle :

```python
page.get_textbox(pymupdf.Rect(cell))
```

Résultat :

```text
['Valeur pedagogique', 'SAN-LAB 2000']
```

### `_clean(text)`

Normalise les espaces et supprime les espaces avant ponctuation :

```python
"Valeur pedagogique ,"  ->  "Valeur pedagogique,"
```

### `_rows_to_markdown(rows)`

Produit un tableau Markdown lisible par le modèle et par l’index :

```markdown
| Champ | Valeur pedagogique |
|---|---|
| Equipement | SAN-LAB 2000 |
```

## 4. `build_chunks(document) -> list[dict]`

Transforme les textes et les tableaux en passages indexables.

### `_split_text(text, size=700, overlap=120)`

Découpe par mots avec chevauchement. Pourquoi :

- un chunk trop grand dilue l’embedding ;
- un chunk trop petit perd le contexte ;
- le chevauchement évite de couper une idée entre deux passages.

Chaque chunk contient :

```python
{
    "chunk_id": "P05-TEXT-C02",
    "source_element_id": "P05-TEXT",
    "page": 5,
    "type": "text",
    "text": "...",
}
```

Un tableau produit un chunk séparé, avec `type="table"`.

## 5. `save_artifacts(document, chunks)`

Écrit :

```text
data/processed/
├── document.json
├── texts.json
├── tables.json
├── chunks.json
├── inventory.csv
└── images/
```

Ces fichiers sont la source unique des notebooks suivants. Ils évitent de
réextraire le PDF à chaque étape.

## 6. `run()` et le CLI

```powershell
uv run python -m maintidoc.ingest
```

Affiche :

```text
Pages : 9
Tableaux : 9
Images : 6
Chunks : 26
```

## 7. OCR optionnel : `src/maintidoc/ocr.py`

Le manuel possède une couche texte : l’OCR n’est pas nécessaire pour le texte
principal. Il est fourni pour les PDF scannés et les libellés des figures.

### `ocr_image(path) -> str`

Utilise RapidOCR et retourne le texte détecté.

### `ocr_figures(images) -> list[dict]`

Ajoute `ocr_text` aux figures, sans modifier les images.

```powershell
uv run python -m maintidoc.ocr
```

Limite : l’OCR peut produire des textes sans espaces
(`FlG-04|Voyants destatut`). Il ne remplace pas une couche texte native.

## 8. Ce qu’il faut retenir

- `get_textbox` est indispensable pour les tableaux de ce PDF.
- Les IDs de page et d’élément sont stables.
- Les tableaux et les figures sont des éléments séparés.
- L’OCR est un fallback, pas la source principale.
