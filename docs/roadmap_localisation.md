# Localisation des cartes de la feuille de route dans le projet

Ce document relie chaque carte de la feuille de route MaintiDoc aux fichiers,
fonctions, artefacts et interfaces du dépôt.

Légende :

- ✅ implémenté ;
- 🟡 partiel ;
- ❌ absent.

---

## Carte 0 — État actuel

| Élément de la carte | Localisation | État |
|---|---|---|
| Manuel SAN pédagogique | `data/raw/Manuel_Maintenance_SAN_Projet_Integrateur.pdf` | ✅ |
| Extraction PyMuPDF | `src/maintidoc/ingest.py:67` — `extract_pdf()` | ✅ |
| Index texte | `src/maintidoc/retrieval.py:39` — `TextIndex` | ✅ |
| Index image | `src/maintidoc/retrieval.py:88` — `ImageIndex` | ✅ |
| Fusion RRF | `src/maintidoc/retrieval.py:142` — `rrf_fuse()` | ✅ |
| Qwen3.8 via Ollama | `src/maintidoc/generation.py:199` — `call_ollama()` ; `src/maintidoc/config.py:28` | 🟡 modèle configurable, Qwen3.8 non installé |
| Notebooks | `notebooks/01_corpus_inventory.ipynb` … `notebooks/06_agentic_rag.ipynb` | ✅ |
| Streamlit | `app.py` | ✅ |

### Précision sur Qwen

Le pipeline est compatible avec tout modèle Ollama. Le modèle par défaut est
`llama3.2:latest` car la GTX 1650 4 Go ne peut pas exécuter Qwen2.5-VL-7B
confortablement. `qwen2.5vl:3b` est installé.

La configuration est dans :

```text
src/maintidoc/config.py:28
```

---

## Carte 1 — Industrialiser le stockage vectoriel

| Exigence | Localisation | État |
|---|---|---|
| Remplacer les index locaux | `src/maintidoc/vector_store.py:84` — `QdrantBundle` | ✅ mode Qdrant |
| Qdrant | `src/maintidoc/vector_store.py:23` — `QdrantStore` | ✅ |
| Séparation index textuel / visuel | `src/maintidoc/vector_store.py:19-20` — `TEXT_COLLECTION`, `IMAGE_COLLECTION` | ✅ |
| Métadonnées et provenance | payloads Qdrant construits dans `QdrantBundle.build()` ; provenance dans `ingest.py` | ✅ |
| Persistance | volume Docker `qdrant_data` ; mode local `data/processed/index/qdrant` | ✅ |
| Mise à jour | `src/maintidoc/bootstrap.py:27` — reconstruit si les collections manquent | 🟡 reconstruction, pas mise à jour incrémentale |
| Démarrage Docker | `docker-compose.yml:4` — service `qdrant` | ✅ |
| Script de construction | `src/maintidoc/vector_store.py:134` — `build_from_local_indexes()` | ✅ |

### Où voir les collections

```text
http://localhost:6333/dashboard
```

```text
maintidoc_text    26 points
maintidoc_images   5 points
```

### Où sont les embeddings locaux

```text
data/processed/index/text_embeddings.npy
data/processed/index/image_embeddings.npy
```

### Documentation

- `docs/retrieval.md`
- `docs/docker.md`

---

## Carte 2 — Améliorer la recherche

| Exigence | Localisation | État |
|---|---|---|
| Recherche hybride texte + image | `src/maintidoc/retrieval.py:233` — `Pipeline.search()` | ✅ |
| Reranker multilingue | `src/maintidoc/rerank.py:16` — `rerank_hits()` | ✅ mais désactivé par défaut |
| Activation du reranker | `app.py` — case « Use multilingual reranker » ; `Pipeline.search(rerank=True)` | ✅ |
| Gestion des tableaux | `src/maintidoc/ingest.py:37` — `_table_rows()` ; `page.get_textbox()` | ✅ |
| OCR | `src/maintidoc/ocr.py:23` — `ocr_image()` ; `:32` — `ocr_figures()` | ✅ optionnel |
| Meilleure sélection des preuves | `src/maintidoc/retrieval.py:164` — `build_evidence()` | ✅ |
| Validation des citations | `src/maintidoc/generation.py:68` — `validate_citations()` ; `:101` — `sanitize_response()` | ✅ structurelle |

### Pourquoi le reranker est désactivé

Sur les 14 questions du corpus :

| Métrique | Sans | Avec |
|---|---:|---:|
| Recall@5 texte | 0,857 | 0,786 |
| Recall@5 RRF | 0,929 | 0,857 |

Il est donc présent mais non activé par défaut. Voir `docs/limites.md`.

### Documentation

- `docs/retrieval.md`
- `docs/generation.md`
- `docs/ingestion.md`

---

## Carte 3 — Ajouter l’orchestration agentique

| Exigence | Localisation | État |
|---|---|---|
| LangGraph | `src/maintidoc/graph.py:40` — `build_graph()` | ✅ |
| État | `src/maintidoc/graph.py:12` — `AgentState` | ✅ |
| Transitions | `src/maintidoc/graph.py:54` — `route()` | ✅ |
| Boucles contrôlées | pas de boucle de reformulation dans `graph.py` | ❌ |
| Clarification | `src/maintidoc/graph.py:63` — `clarify()` | ✅ |
| Stratégie outillée | le graphe ne contient que le RAG ; MCP est dans l’onglet séparé | 🟡 |
| Lancement | `src/maintidoc/graph.py:81` — `run_agent()` | ✅ |
| Interface | `app.py:121` — onglet « LangGraph agent » | ✅ |
| Notebook | `notebooks/06_agentic_rag.ipynb` | ✅ |

### Ce qui est réellement implémenté

```text
retrieve → generate → route
                         ├── finalize
                         └── clarify
```

### Ce qui manque pour la carte complète

- boucle de reformulation si les preuves sont faibles ;
- appels MCP depuis le graphe ;
- persistance d’état ;
- `interrupt()` LangGraph pour l’approbation humaine ;
- stratégie multi-outils.

Voir `docs/agent.md` et `docs/limites.md`.

---

## Carte 4 — Connecter MCP

| Exigence | Localisation | État |
|---|---|---|
| `get_equipment_history()` | `src/maintidoc/mcp_server.py:22` ; `src/maintidoc/mcp_store.py:68` | ✅ |
| `get_open_tickets()` | `src/maintidoc/mcp_server.py:28` ; `src/maintidoc/mcp_store.py:75` | ✅ |
| `create_ticket(...)` | `src/maintidoc/mcp_server.py:34` ; `src/maintidoc/mcp_store.py:124` | ✅ |
| Validation humaine obligatoire | `src/maintidoc/mcp_store.py:103` — `approve_ticket()` | ✅ |
| Idempotence | `src/maintidoc/mcp_store.py:124` — `idempotency_key` | ✅ |
| Traçabilité | `data/mock/audit.jsonl` ; `_audit()` dans `mcp_store.py` | ✅ |
| Serveur MCP | `src/maintidoc/mcp_server.py` ; `mcp_server.py` | ✅ |
| Client MCP | `src/maintidoc/mcp_calls.py` ; `mcp_client.py` | ✅ |
| Interface | `app.py:175` — onglet « MCP tickets » | ✅ |
| Notebook | `notebooks/05_mcp_demo.ipynb` | ✅ |
| Tests | `tests/test_mcp.py` | ✅ |

### Flux

```text
prepare_ticket()
  → brouillon
  → approve_ticket()
  → approval_token
  → create_ticket()
  → ticket + audit
```

### Limites

- données JSON mock ;
- pas d’authentification/RBAC ;
- MCP n’est pas appelé depuis LangGraph ;
- PostgreSQL/MinIO sont provisionnés mais non branchés au serveur MCP.

Voir `docs/mcp.md`.

---

## Correspondances interface

| Onglet Streamlit | Ligne | Fonction |
|---|---:|---|
| Search & answer | `app.py:49` | recherche + génération |
| LangGraph agent | `app.py:121` | `run_agent()` |
| MCP tickets | `app.py:175` | `call_tool()` |
| Corpus | `app.py:243` | inventaire + figures |

---

## Correspondances Docker

| Service | Ligne dans `docker-compose.yml` |
|---|---:|
| `qdrant` | 4 |
| `postgres` | 15 |
| `adminer` | 35 |
| `minio` | 48 |
| `app` | 62 |
| `mlflow` | 90 |

---

## Correspondances documentation

| Sujet | Document |
|---|---|
| Ingestion, tableaux, OCR | `docs/ingestion.md` |
| BGE-M3, CLIP, Qdrant, RRF, reranker | `docs/retrieval.md` |
| Génération et citations | `docs/generation.md` |
| LangGraph | `docs/agent.md` |
| MCP | `docs/mcp.md` |
| Docker et base | `docs/docker.md` |
| Évaluation | `docs/evaluation.md` |
| Architecture complète | `docs/architecture_complete.md` |

---

## Synthèse

| Carte | État global |
|---|---|
| État actuel | ✅ |
| 1 — Stockage vectoriel | ✅ sauf mise à jour incrémentale |
| 2 — Recherche | ✅ avec reranker optionnel |
| 3 — Orchestration agentique | 🟡 LangGraph oui, boucle/outils non |
| 4 — MCP | ✅ démonstrateur, pas production |
