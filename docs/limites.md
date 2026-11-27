# Limites du prototype

## 1. Périmètre

- Corpus **fictif** : SAN-LAB 2000 n'existe pas.
- Une seule famille d'équipements, un seul manuel de 9 pages.
- Le CDC prévoit 30 à 50 documents ; ce n'est pas le cas ici.
- Le système est **documentaire** : il ne pilote aucun équipement.

## 2. Extraction

- `table.extract()` perdait les espaces ; la correction utilise `get_textbox`.
- Certaines cellules de tableau peuvent encore contenir des artefacts de mise en page.
- Les figures sont des images raster ; un schéma vectoriel ne serait pas extrait
  par `get_images()`.
- La page 8 est une page de séparation sans contenu.
- L'OCR est optionnel et peut produire des textes sans espaces.

## 3. Stockage et recherche

- Qdrant est utilisé en **mode local fichier**, pas en serveur Qdrant.
- Les collections texte et image sont séparées, avec métadonnées et provenance.
- La fusion est **au niveau des pages**, pas des éléments.
- CLIP ViT-B/32 est surtout anglophone : la requête visuelle est écrite en anglais.
- Un score CLIP est une similarité, pas une probabilité.
- Le reranker multilingue est inclus mais **désactivé par défaut** : sur 14
  questions, il dégrade le rappel (0,786 au lieu de 0,857 en Recall@5 texte).
- `Recall@3` figures = 0,714 : insuffisant pour la production.

## 4. Génération

- Modèle par défaut : `llama3.2:latest`, qui n'est **pas** un VLM.
- L’upload d’image utilise `qwen2.5vl:3b` ; la GTX 1650 4 Go est très juste.
- Les images sont affichées mais ne sont pas toujours transmises au modèle.
- Qwen2.5-VL-7B est prévu par le CDC mais n'est pas installé par défaut.
- Un petit modèle peut citer un identifiant documentaire au lieu d'un identifiant
  de preuve ; les citations inconnues sont filtrées.
- Le fallback extractif est moins fluide : il sert à garantir la démonstration.

## 5. Citations

- La validation est **structurelle** : l'ID et la page existent.
- Elle ne prouve pas que le passage **soutient** l'affirmation.
- La vérification sémantique reste manuelle ou à instrumenter.
- L'objectif de 90 % de citations soutenantes n'est pas mesuré ici.

## 6. MCP

- Données **mock** (JSON), pas de vraie base.
- Pas d'authentification, pas de RBAC.
- Le jeton d'approbation est simulé par `approve_ticket()`.
- L'idempotence est locale.
- Le journal d'audit est un fichier JSONL.
- Le workflow LangGraph est linéaire avec une seule boucle de clarification ;
  pas de vraie stratégie multi-outils.

## 7. Évaluation

- 14 questions, pas 150 scénarios.
- Pas d'annotations de soutien sémantique.
- Pas de mesure de latence p95.
- Pas de tests d'injection de prompt.
- Pas de comparaison texte seul / multimodal à grande échelle.

## 8. Ce qu'il faudrait ajouter

1. Qdrant en **serveur** ou PGVector.
2. Reranker activé et calibré sur un corpus plus large.
3. FastAPI + authentification + RBAC.
4. LangGraph avec état persistant et interruptions humaines.
5. Prompts YAML versionnés.
6. Jeu de 150 scénarios.
7. Fine-tuning du reranker.
8. Docker Compose + MLflow.
