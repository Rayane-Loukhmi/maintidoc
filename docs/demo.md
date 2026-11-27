# Scénario de démonstration (5–8 minutes)

## 1. Corpus

Ouvrir `notebooks/01_corpus_inventory.ipynb` et montrer :

- 9 pages ;
- 5 schémas + couverture ;
- 9 tableaux ;
- page 8 = séparation.

Message : le corpus est compris avant de construire le RAG.

## 2. Extraction

Ouvrir `notebooks/02_extraction_chunks.ipynb` et montrer :

- `table.extract()` vs `get_textbox()` ;
- les cellules propres (`Valeur pedagogique`, `SAN-LAB 2000`) ;
- 26 passages indexables.

Message : la qualité de l'extraction conditionne tout le reste.

## 3. Recherche multimodale

Ouvrir `notebooks/03_rag_multimodal.ipynb` et exécuter la question :

```text
Que signifie le voyant orange AL-01 ?
```

Montrer :

- les passages BGE-M3 ;
- les figures CLIP ;
- la fusion RRF ;
- les métriques : Recall@5 = 0,857 ; RRF = 0,929.

Message : le texte et l'image sont deux canaux, fusionnés par rang.

## 4. Réponse sourcée

Ouvrir `notebooks/04_generation_citations.ipynb` et montrer :

- le prompt avec IDs autorisés ;
- la réponse JSON ;
- la citation `P05-TAB01` page 5 ;
- le filtrage d'une citation inconnue ;
- le fallback si le modèle est absent.

Message : la réponse est traçable ; une citation inconnue est retirée.

## 5. MCP

Ouvrir `notebooks/05_mcp_demo.ipynb` et montrer :

1. `list_tools()` : 3 outils ;
2. `get_equipment_history` : 4 interventions ;
3. `prepare_ticket` : brouillon ;
4. `approve_ticket` : jeton lié au hash ;
5. `create_ticket` : ticket créé ;
6. deuxième appel : `idempotent: True` ;
7. jeton invalide : refus ;
8. `audit.jsonl`.

Message : aucune création sans approbation humaine, aucun doublon.

## 6. Industrialisation

Ouvrir `notebooks/06_agentic_rag.ipynb` et montrer :

- Qdrant local (collections texte/image) ;
- reranker multilingue (optionnel, désactivé par défaut) ;
- OCR d'une figure ;
- agent LangGraph `retrieve → generate → validate → clarify`.

Message : les étapes 1, 2 et 3 de la feuille de route sont couvertes.

## 7. Architecture

Afficher :

- `docs/architecture_globale.png` ;
- `docs/architecture_mcp.png`.

Message : le prototype est un système, pas un prompt.

## 8. Limites

Annoncer clairement :

- corpus fictif ;
- pas d'authentification/RBAC ;
- Qdrant en mode local (pas serveur) ;
- LangGraph simple, sans boucle multi-outils ;
- validation sémantique des citations encore manuelle.

## Plan B si Ollama ne répond pas

Le notebook 04 passe en mode `fallback` : réponse extractive avec citation.
Le notebook 05 ne dépend pas d'Ollama.
