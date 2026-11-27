# Agent LangGraph

Ce document décrit `src/maintidoc/graph.py`.

## 1. Pourquoi un graphe

Un pipeline linéaire suffit pour :

```text
question → recherche → réponse
```

Mais il ne gère pas :

- la décision de répondre ou de demander une clarification ;
- l’état intermédiaire ;
- l’ajout futur d’outils MCP ;
- les transitions conditionnelles.

LangGraph modélise ces décisions comme un **graphe d’états**.

## 2. `AgentState`

```python
class AgentState(TypedDict, total=False):
    question: str
    visual_query: str
    retrieval: dict
    answer: dict
    route: str
```

L’état transporte les données entre les nœuds.

## 3. Les nœuds

### `retrieve`

- appelle `Pipeline.search(question, visual_query, rerank=False)` ;
- stocke `retrieval` (preuves, pages, images).

### `generate`

- appelle `answer_question(...)` ;
- stocke `answer` ;
- force `mode="langgraph"`.

### `route`

Route conditionnelle :

```python
if answer.status == "answered" and answer.citations:
    return "finalize"
return "clarify"
```

### `finalize`

Nœud terminal : la réponse est déjà complète.

### `clarify`

Produit un message de clarification :

```text
I cannot support a reliable answer with the retrieved evidence.
Please provide the exact alarm code, the equipment model, or a sharper photo.
```

Pourquoi : une absence de preuve ne doit pas devenir une invention.

## 4. `build_graph(pipeline, model, language)`

Construit :

```text
retrieve → generate → route
                         ├── finalize → END
                         └── clarify  → END
```

Le graphe est compilé avec `StateGraph(...).compile()`.

## 5. `run_agent(question, visual_query, model, language, pipeline=None)`

- charge Qdrant si aucun pipeline n’est fourni ;
- compile le graphe ;
- invoque l’état initial ;
- retourne l’état final.

Exemple :

```python
result = run_agent(
    "What does the orange AL-01 LED mean?",
    "orange warning LED storage array front panel",
    model="llama3.2:latest",
    language="en",
)
print(result["answer"]["status"])
```

Résultat attendu : `answered` + citation page 5.

## 6. Clarification testée

```python
run_agent("What is the price of the SAN-LAB 2000?", ...)
```

Résultat :

```text
needs_clarification
```

Pourquoi : le manuel ne contient pas de prix. Le graphe ne doit pas inventer.

## 7. Limites

- Une seule passe de retrieval ; pas de boucle de reformulation.
- Pas d’outil MCP dans le graphe pour l’instant.
- Pas de persistance d’état entre sessions.
- Pas de `interrupt()` LangGraph pour l’approbation humaine : l’approbation est
  gérée par l’application et MCP.
- Le graphe est volontairement simple pour rester démontrable.

## 8. Ce qu’il faut retenir

- Le graphe rend la décision `answer` / `clarify` explicite.
- L’état est typé.
- Le routeur est déterministe : il vérifie le statut et les citations.
- C’est une base pour ajouter des outils MCP et des boucles bornées.
