# Recherche multimodale, Qdrant, RRF et reranker

Ce document décrit `src/maintidoc/retrieval.py`, `src/maintidoc/vector_store.py`
et `src/maintidoc/rerank.py`.

## 1. Deux index, deux modèles

| Index | Modèle | Dimension | Objet |
|---|---|---:|---|
| Texte | BGE-M3 | 1024 | passages et tableaux |
| Image | CLIP ViT-B/32 | 512 | schémas |

Pourquoi deux index :

- BGE-M3 est multilingue et adapté au texte français ;
- CLIP aligne texte et image, mais est surtout anglophone ;
- les scores ne sont pas comparables.

## 2. `TextIndex`

### `TextIndex.build(chunks)`

- encode chaque `chunk["text"]` avec BGE-M3 ;
- normalise les vecteurs ;
- sauvegarde `text_embeddings.npy` et `text_chunks.json`.

### `TextIndex.load()`

Recharge les vecteurs et les chunks sans recalcul.

### `TextIndex.search(query, top_k=6)`

Calcule :

$$
\operatorname{sim}(q,d)=\frac{q\cdot d}{\|q\|\|d\|}
$$

puis retourne les `top_k` passages avec :

- `page` ;
- `element_id` ;
- `type` ;
- `text` ;
- `score` (similarité, pas probabilité).

## 3. `ImageIndex`

### `ImageIndex.build(images)`

Filtre `kind == "figure"` (donc exclut `COVER`), encode les 5 schémas avec CLIP
et sauvegarde `image_embeddings.npy` et `image_manifest.json`.

### `ImageIndex.search(query, top_k=5)`

Compare une requête textuelle anglaise aux vecteurs d’images.

Un score CLIP élevé signifie « proche dans l’espace CLIP », pas « le schéma
répond à la question ».

## 4. Qdrant local

`src/maintidoc/vector_store.py` fournit :

```python
QdrantBundle
QdrantTextIndex
QdrantImageIndex
build_from_local_indexes()
load_bundle()
```

### Collections

```text
maintidoc_text    26 points · 1024 dimensions · cosine
maintidoc_images   5 points ·  512 dimensions · cosine
```

Chaque point contient les métadonnées nécessaires aux citations : `chunk_id`,
`element_id`, `page`, `type`, `text`, `path`.

### Mode local

```python
QdrantClient(path="data/processed/index/qdrant")
```

Ce n’est pas un serveur Qdrant : c’est le moteur Qdrant en mode fichier. Il permet
de tester la persistance et l’API sans Docker.

### `build_from_local_indexes()`

Construit les deux collections à partir des embeddings `.npy` déjà calculés.

```powershell
uv run python -m maintidoc.vector_store
```

## 5. Fusion RRF

### `rrf_fuse(text_hits, image_hits, k=60, top_pages=4)`

Formule :

$$
\operatorname{RRF}(d)=\sum_{r\in R(d)}\frac{1}{k+\operatorname{rank}_r(d)}
$$

Pourquoi les rangs :

- un score BGE-M3 et un score CLIP n’ont pas la même échelle ;
- additionner les scores serait arbitraire ;
- fusionner les rangs est robuste.

La fusion est faite **au niveau des pages**. C’est volontairement simple : une
figure et son explication textuelle sont souvent sur la même page.

## 6. Dossier de preuves

### `build_evidence(text_hits, image_hits, pages, max_chars=8500, max_images=1)`

- sélectionne les passages des pages retenues ;
- borne le nombre de caractères ;
- choisit au plus une image, en priorité sur la page la mieux classée ;
- conserve `id`, `page`, `type`, `content`.

Pourquoi borner :

- mémoire ;
- latence ;
- qualité du contexte ;
- coût des images dans le prompt.

## 7. `Pipeline`

### `Pipeline.load_or_build(..., backend="numpy")`

- `backend="qdrant"` : charge les collections Qdrant ;
- sinon : charge les index `.npy` ;
- sinon : reconstruit les index.

### `Pipeline.search(question, visual_query, rerank=False)`

1. recherche texte (12 candidats si reranker, 6 sinon) ;
2. reranking éventuel ;
3. recherche image ;
4. fusion RRF ;
5. construction des preuves.

## 8. Reranker

### `rerank_hits(question, hits, top_k=6)`

Utilise un **cross-encoder** :

```text
cross-encoder/mmarco-mMiniLMv2-L12-H384-v1
```

Il lit la paire `(question, passage)` et produit un score de pertinence.

Différence :

| Type | Entrée | Rapidité | Précision |
|---|---|---|---|
| Bi-encoder (BGE-M3) | question et passage séparément | rapide | bonne |
| Cross-encoder | paire complète | lente | meilleure en général |

### Pourquoi il est désactivé par défaut

Sur les 14 questions du corpus :

| Métrique | Sans | Avec |
|---|---:|---:|
| Recall@5 texte | **0,857** | 0,786 |
| Recall@5 RRF | **0,929** | 0,857 |

Le reranker dégrade le rappel sur ce petit corpus. Il reste disponible pour
expérimentation, mais n’est pas activé par défaut.

## 9. Ce qu’il faut retenir

- BGE-M3 et CLIP sont deux canaux distincts.
- Qdrant sépare les collections texte et image.
- RRF fusionne des rangs, pas des scores.
- Le reranker est un cross-encoder optionnel.
- La fusion par page est un choix de prototype.
