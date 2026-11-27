# Évaluation de la recherche

Ce document décrit `eval/run_eval.py`, `eval/questions.jsonl` et
`eval/results.csv`.

## 1. Pourquoi un jeu de questions

Sans références annotées, on ne peut pas dire si une modification améliore le
système. Le jeu de 14 questions sert de **banc d’essai minimal**.

## 2. `eval/questions.jsonl`

Chaque ligne contient :

```json
{
  "id": "Q05",
  "question": "Quel est le sens de AL-01 ?",
  "visual_query": "orange warning LED storage array front panel",
  "expected_pages": [5],
  "expected_figures": ["FIG-04"],
  "expected_status": "answered",
  "category": "image+table"
}
```

Catégories :

- texte ;
- texte + image ;
- image ;
- table ;
- question sans réponse.

## 3. `eval/run_eval.py`

Pour chaque question :

1. appelle `Pipeline.search` ;
2. récupère les pages top 5 et les figures top 3 ;
3. calcule les métriques ;
4. écrit `eval/results.csv`.

### `recall(expected, found)`

```python
len(set(expected) & set(found)) / len(set(expected))
```

### `recall_text@5`

Proportion de pages attendues présentes dans les 5 premières pages texte.

### `recall_rrf`

Proportion de pages attendues présentes dans les pages fusionnées.

### `recall_image@3`

Proportion de figures attendues présentes dans les 3 premières figures CLIP.

### `mrr_page`

Moyenne de l’inverse du rang de la première page pertinente.

## 4. Résultats

Avec les index `.npy` et sans reranker :

| Métrique | Valeur |
|---|---:|
| Recall@5 texte | 0,857 |
| Recall@5 RRF | 0,929 |
| Recall@3 figures | 0,714 |
| MRR page | 0,667 |

Avec reranker :

| Métrique | Valeur |
|---|---:|
| Recall@5 texte | 0,786 |
| Recall@5 RRF | 0,857 |
| Recall@3 figures | 0,714 |
| MRR page | 0,598 |

## 5. Ce que ces scores ne disent pas

- Ils ne mesurent pas la **qualité sémantique** de la réponse.
- Ils ne mesurent pas le **soutien réel** des citations.
- Ils ne mesurent pas la latence.
- Ils ne mesurent pas la sécurité.
- Le corpus est petit : 14 questions, 9 pages.

## 6. Comment relancer

```powershell
uv run python eval/run_eval.py
```

Le script reconstruit les index si nécessaire, puis écrit `eval/results.csv`.

## 7. Ce qu’il faut retenir

- Le rappel RRF est meilleur que le rappel texte seul.
- Le rappel image est le point faible (0,714).
- Le reranker n’améliore pas ce corpus.
- Ces résultats sont un point de départ, pas une validation de production.
