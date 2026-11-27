# Génération sourcée et validation des citations

Ce document décrit `src/maintidoc/generation.py`.

## 1. Objectif

Transformer un dossier de preuves en réponse **JSON** contenant :

- un statut ;
- une réponse ;
- des citations ;
- des incertitudes.

Le modèle ne doit pas répondre de mémoire. Il doit utiliser les preuves
transmises, et les citations doivent être vérifiables.

## 2. `build_prompt(question, evidence, language="fr", image_description=None)`

Construit le message utilisateur :

```text
Question : ...
Answer in English. / Réponds en français.

PREUVES :
[P05-TEXT | page 5 | text]
...

[P05-TAB01 | page 5 | table]
| Code | Etat | ... |

IDs autorisés : [{"id": "P05-TEXT", "page": 5, "type": "text"}, ...]
```

Pourquoi afficher les IDs autorisés :

- le modèle doit citer un ID de preuve, pas un identifiant documentaire ;
- les IDs sont la seule base de validation ;
- cela réduit les citations inventées.

### Photo uploadée

Si la question contient une photo, le VLM produit une description :

```text
DESCRIPTION OF THE PHOTO UPLOADED BY THE TECHNICIAN
(observational context, not a documentary source)
```

Cette description est ajoutée au prompt, mais **elle ne remplace pas les preuves**.
Le modèle doit toujours citer une page ou une figure du corpus.

Le VLM utilisé est `qwen2.5vl:3b` via `src/maintidoc/vision.py`.

## 3. `call_ollama(question, evidence, images=None, model=..., language="fr")`

Appelle Ollama avec :

```python
format="json"
temperature=0
num_ctx=4096
num_predict=700
```

Les images ne sont transmises que si le modèle est un VLM
(`vl`, `vision`, `llava` dans le nom). `llama3.2` est texte seul.

## 4. `_extract_json(raw)`

Isole le premier objet JSON entre `{` et `}`. Pourquoi :

- un petit modèle ajoute parfois du texte avant/après ;
- `json.loads` échouerait sur le texte parasite.

## 5. `validate_citations(response, evidence)`

Vérifie :

- `status` parmi `answered`, `needs_clarification`, `insufficient_evidence` ;
- `answer` non vide ;
- `citations` est une liste ;
- une réponse `answered` a au moins une citation ;
- chaque `(id, page)` existe dans les preuves.

C’est une validation **structurelle**.

## 6. `sanitize_response(response, evidence)`

Un petit modèle peut citer `ALARM-TAB-01` (identifiant documentaire) au lieu de
`P05-TAB01` (identifiant de preuve).

La fonction :

- conserve les citations valides ;
- retire les citations inconnues ;
- ajoute une incertitude si des citations ont été retirées ;
- passe le statut à `needs_clarification` si aucune citation valide ne reste.

Pourquoi filtrer plutôt que rejeter :

- une réponse peut être bonne avec une citation parasite ;
- on garde la traçabilité de l’incident ;
- on ne laisse pas une fausse citation dans la réponse finale.

## 7. `fallback_answer(question, evidence, reason, language="fr")`

Réponse extractive si Ollama est indisponible ou si le JSON est invalide :

- choisit la première preuve non-image ;
- renvoie une réponse courte ;
- cite cette preuve ;
- signale que le modèle n’a pas été utilisé.

Ce n’est pas une réponse de production. C’est une garantie de démonstration.

## 8. `answer_question(question, retrieval, model=..., language="fr")`

Pipeline complet :

```text
call_ollama
  → _extract_json
  → sanitize_response
  → validate_citations
  → fallback si exception
```

Retour :

```python
{
    "status": "answered",
    "answer": "...",
    "citations": [{"id": "P05-TAB01", "page": 5}],
    "uncertainties": [],
    "issues": [],
    "mode": "ollama" | "fallback",
    "model": "...",
    "raw": "...",
}
```

## 9. Statuts

| Statut | Signification |
|---|---|
| `answered` | réponse soutenue par au moins une preuve |
| `needs_clarification` | information manquante ou ambiguë |
| `insufficient_evidence` | aucune preuve pertinente |

Le système ne produit **pas** de pourcentage de confiance. Les probabilités d’un
LLM ne sont pas calibrées.

## 10. Ce qu’il faut retenir

- Le prompt contient les IDs autorisés.
- La validation est structurelle.
- Les citations inconnues sont filtrées.
- Le fallback garantit la démo.
- La validation sémantique reste manuelle.
