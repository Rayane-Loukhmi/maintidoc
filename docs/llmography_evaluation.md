# Évaluation LLMography — projet MaintiDoc

**Méthode :** LLMography, Mohammed Bousmah, arXiv:2606.29437  
**Objet évalué :** projet MaintiDoc et trajectoire de collaboration Humain–IA  
**Date :** 2026-11-27  
**Nature :** évaluation reconstruite à partir du dépôt, des tests, des notebooks,
des documents et de l’historique de la session. Ce n’est pas un audit certifié
LLMography.ai, faute d’export complet de la conversation.

Référence : [LLMography: Transforming Human–AI Conversations into Traceability,
Oversight, and Auditability Indicators](https://arxiv.org/abs/2606.29437)

---

## 1. Principe appliqué

LLMography ne juge pas seulement le résultat final. Il évalue :

- la direction humaine ;
- la qualité des prompts ;
- la dépendance à l’IA ;
- l’auditabilité ;
- la traçabilité du résultat ;
- le risque de confidentialité.

> « LLMography does not judge whether AI was used. It explains how AI was used. »

L’évaluation porte donc sur **le processus de co-construction**, pas uniquement
sur la qualité du code.

---

## 2. Base de preuves

| Preuve | Ce qu’elle montre |
|---|---|
| Dépôt `maintidoc/` | 6 notebooks, 5 modules RAG, MCP, Docker, docs |
| `docs/architecture_complete.md` | architecture et cartographie des fichiers |
| `README.md` | lancement, limites, résultats |
| `tests/` | 9 tests automatisés |
| `eval/results.csv` | métriques de retrieval |
| `docker-compose.yml` | PostgreSQL, Qdrant, Adminer, MinIO, app |
| historique de la session | demandes, corrections, refus, arbitrages |
| `audit.jsonl` | traçabilité des actions MCP |
| `docs/decisions.md` | décisions techniques |

### Limites de la base de preuves

- pas d’export complet de la conversation ;
- pas de commits Git (dépôt initialisé mais aucun commit) ;
- les prompts exacts ne sont pas tous conservés ;
- les allers-retours de débogage ne sont pas tous visibles ;
- l’évaluation est donc une **reconstruction**, pas une preuve exhaustive.

---

## 3. Résultats KPI

Échelle LLMography : 0–20 très faible, 21–40 faible, 41–60 modéré,
61–80 bon, 81–100 fort.

| KPI | Score | Niveau | Justification |
|---|---:|---|---|
| **Prompt Quality** | **86/100** | fort | objectifs explicites, contraintes techniques, corrections successives |
| **Human Direction** | **90/100** | fort | choix de stack, refus du 7B, exigence Docker, UI anglaise, priorisation |
| **Human Oversight** | **88/100** | fort | tests, relecture, corrections, vérification des étapes |
| **AI Dependency** | **70/100** | modéré–élevé | l’IA a produit l’essentiel du code et de la documentation |
| **Auditability** | **78/100** | bon | docs, tests, logs, architecture ; mais pas de commits ni transcript |
| **Final Output Traceability** | **82/100** | fort | mapping exigences → modules → docs, citations, tests |
| **Reproducibility** | **82/100** | fort | `uv.lock`, Docker Compose, scripts, notebooks |
| **Privacy Risk** | **8/100** | très faible | corpus fictif, données locales, pas de données personnelles |

> `AI Dependency` et `Privacy Risk` sont des niveaux LLMography. Les valeurs
> numériques sont des équivalents indicatifs, utilisés ici pour la comparaison.

---

## 4. Label LLMography

### Label recommandé : **C — Human–AI co-produced**

**Caractérisation précise :**

> Projet originé par l’humain, fortement dirigé par l’humain, avec une exécution
> technique majoritairement assistée par l’IA.

Pourquoi C et non B :

- l’humain a défini le problème, les contraintes, les priorités et les arbitrages ;
- l’IA a produit une grande partie du code, des tests, des notebooks et de la
  documentation ;
- la validation humaine est réelle mais pas intégralement ligne par ligne ;
- le résultat est une co-production, pas une simple assistance ponctuelle.

Pourquoi C et non D :

- l’humain a refusé des choix inadaptés (Qwen 7B sur 4 Go de VRAM) ;
- il a imposé Docker, PostgreSQL, l’interface anglaise et la documentation ;
- il a demandé des vérifications et des corrections ;
- il a conservé la responsabilité du périmètre.

---

## 5. Analyse qualitative

### 5.1 Points forts

1. **Direction humaine explicite**
   - choix de l’architecture ;
   - refus d’un modèle trop lourd ;
   - exigence de Docker et de base de données ;
   - exigence de documentation par concept.

2. **Prompts contextualisés**
   - contraintes de langue ;
   - contraintes matérielles ;
   - contraintes de livrable ;
   - demandes de vérification.

3. **Traçabilité du résultat**
   - IDs de preuve (`P05-TAB01`) ;
   - citations page/élément ;
   - architecture complète ;
   - tests automatisés ;
   - journal MCP.

4. **Boucle de correction**
   - erreurs d’encodage corrigées ;
   - UI traduite en anglais ;
   - affichage des preuves ajouté dans LangGraph ;
   - Qdrant, reranker, OCR et LangGraph intégrés après revue.

5. **Séparation des responsabilités**
   - l’IA propose ;
   - l’humain arbitre ;
   - les tests vérifient ;
   - MCP exige une approbation humaine.

### 5.2 Faiblesses

1. **Pas d’historique Git**
   - aucun commit ;
   - impossible de reconstruire les étapes par diff.

2. **Pas de journal de prompts**
   - les prompts exacts ne sont pas versionnés ;
   - les corrections ne sont pas toutes tracées.

3. **Dépendance à l’IA encore élevée**
   - beaucoup de code généré ;
   - l’humain a surtout validé et orienté.

4. **Validation sémantique des citations incomplète**
   - validation structurelle seulement ;
   - pas d’annotation de soutien.

5. **Traçabilité des essais**
   - pas de journal des tests avant/après ;
   - pas de tableau de bord des métriques.

### 5.3 Risques

| Risque | Niveau | Commentaire |
|---|---|---|
| dépendance excessive à l’IA | modéré | l’humain garde la direction, mais l’exécution est très assistée |
| provenance incomplète | modéré | pas de transcript ni de commits |
| sécurité | modéré | pas d’auth/RBAC, credentials de dev |
| confidentialité | faible | corpus fictif, données locales |
| surconfiance dans les citations | modéré | validation structurelle seulement |

---

## 6. Comparaison aux moyennes LLMography

Le papier rapporte, sur 19 rapports d’étudiants :

| KPI | Moyenne du papier | MaintiDoc |
|---|---:|---:|
| Prompt Quality | 81,9 | **86** |
| Human Direction | 86,8 | **90** |
| Auditability | 72,8 | **78** |
| Final Output Traceability | 77,1 | **82** |

MaintiDoc se situe légèrement au-dessus des moyennes, mais la comparaison est
indicative : un seul projet, une trace reconstruite, pas un panel de 19.

---

## 7. Ce qui améliorerait le score LLMography

### Auditabilité

- [ ] faire un premier commit Git ;
- [ ] commits atomiques par étape ;
- [ ] conserver `docs/decisions.md` à jour ;
- [ ] exporter un journal de prompts ;
- [ ] ajouter un fichier `TRACE.md` reliant exigence → fichier → test.

### Traçabilité

- [ ] matrice exigence → module → test ;
- [ ] lier chaque réponse RAG à ses preuves ;
- [ ] conserver les résultats d’évaluation avant/après ;
- [ ] versionner les prompts.

### Direction humaine

- [ ] documenter les arbitrages et refus ;
- [ ] ajouter une revue de code humaine ;
- [ ] conserver les corrections manuelles.

### Sécurité

- [ ] ne pas versionner `.env` ;
- [ ] remplacer les credentials de dev ;
- [ ] ajouter auth/RBAC avant production.

---

## 8. Évaluation technique hors LLMography

LLMography évalue le processus, pas la qualité du code. Pour compléter :

| Dimension | Note | Commentaire |
|---|---:|---|
| Architecture | 8/10 | couches claires, Docker, MCP |
| Code | 7,5/10 | modules lisibles, mais duplication notebook/package |
| Tests | 7/10 | 9 tests, pas d’intégration Docker/DB |
| Documentation | 9/10 | très complète |
| Sécurité | 5/10 | pas d’auth/RBAC, credentials de dev |
| Évaluation RAG | 6/10 | 14 questions, pas 150 |
| Multimodal | 6/10 | CLIP + retrieval, mais pas de VLM 7B |
| MCP | 8/10 | outils, HITL, idempotence, audit |
| Docker | 8/10 | stack fonctionnelle, MinIO partiel |

---

## 9. Verdict

**Label : C — Human–AI co-produced.**

MaintiDoc est un projet :

- **originé par l’humain** ;
- **fortement dirigé par l’humain** ;
- **techniquement exécuté avec une assistance IA importante** ;
- **auditable partiellement** ;
- **traçable dans ses artefacts** ;
- **à faible risque de confidentialité**.

Le principal point faible LLMography n’est pas la qualité du résultat, mais la
**traçabilité du processus** : absence de commits, de journal de prompts et
d’export complet de conversation.

La phrase de synthèse :

> MaintiDoc obtient un profil LLMography solide sur la direction humaine et la
> traçabilité du résultat, mais sa note d’auditabilité est limitée par l’absence
> d’historique Git et de journal de prompts.
