# Journal des décisions — MaintiDoc

## 1. Décisions techniques

| Décision | Choix | Pourquoi | Statut |
|---|---|---|---|
| Gestionnaire Python | `uv` | lockfile, Python 3.12, Docker | décidé |
| Version Python | 3.12 | compatibilité PyMuPDF / PyTorch / Transformers | décidé |
| Parseur PDF | PyMuPDF | déjà utilisé par le prototype | décidé |
| Extraction tableaux | `get_textbox(Rect(cell))` | conserve les espaces | décidé |
| Embedding texte | BGE-M3 | multilingue, 1024 dimensions | décidé |
| Embedding image | CLIP ViT-B/32 | 512 dimensions, prototype | décidé |
| Stockage vectoriel | Qdrant local persistant | collections texte/image séparées | décidé |
| Reranker | cross-encoder mmarco | multilingue, optionnel | décidé |
| Reranker par défaut | désactivé | dégrade le rappel sur 14 questions | décidé |
| OCR | RapidOCR | optionnel, figures/PDF scannés | décidé |
| Orchestration | LangGraph | état, transitions, clarification | décidé |
| Fusion | RRF par page | scores non comparables | décidé |
| Génération | Ollama `llama3.2:latest` | disponible localement | décidé |
| Génération cible | `qwen2.5vl:7b` | multimodal complet | à installer |
| Interface | Streamlit | prototypage rapide | décidé |
| MCP | SDK `mcp` 2.x, `MCPServer` | API actuelle | décidé |
| Transport MCP | stdio | local, sans port | décidé |
| Stockage MCP | JSON mock | démonstration | décidé |
| Validation citations | structurelle + filtrage | IDs et pages | décidé |
| Fallback | réponse extractive | démo sans modèle | décidé |

## 2. Décisions de périmètre

| Décision | Choix | Pourquoi | Statut |
|---|---|---|---|
| Corpus | 1 manuel, 9 pages | prototype | décidé |
| Corpus cible | 30–50 documents | CDC | plus tard |
| Utilisateurs | techniciens | CDC | décidé |
| Action sensible | ticket après approbation | sécurité | décidé |
| Hors périmètre | pilotage, diagnostic garanti | documentaire | décidé |

## 3. Format

| Décision | Choix | Pourquoi | Statut |
|---|---|---|---|
| Réponse | JSON | structuré | décidé |
| Statuts | `answered`, `needs_clarification`, `insufficient_evidence` | incertitude | décidé |
| Citation | `id`, `page` | traçabilité | décidé |
| Prompt | `prompts/answer_v1.txt` | versionné | décidé |

## 4. Points ouverts

| Point | Question | Statut |
|---|---|---|
| Base vectorielle | Qdrant ou PGVector | à trancher |
| Reranker | préentraîné ou fine-tuné | à trancher |
| VLM | Qwen2.5-VL-7B | à installer |
| Authentification | FastAPI + RBAC | plus tard |
| Orchestration | LangGraph | plus tard |
| Évaluation | 150 scénarios | plus tard |

## 5. Règles

- Une décision est datée dans le rapport final.
- Aucun secret dans ce fichier.
- Les choix non tranchés restent « à trancher ».
