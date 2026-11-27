# Guide d’utilisation de l’application MaintiDoc

Ce guide explique comment lancer et utiliser l’application Streamlit.

L’interface est en **anglais**. Les réponses générées dans l’application sont en
anglais ; les notebooks et leurs explications restent en français.

---

## 1. Ce que fait l’application

MaintiDoc permet de :

1. poser une question sur le manuel SAN fictif ;
2. rechercher dans le texte et les schémas ;
3. afficher les preuves utilisées ;
4. générer une réponse avec citations ;
5. exécuter un agent LangGraph ;
6. consulter l’historique et préparer un ticket via MCP ;
7. approuver un ticket avant sa création.

---

## 2. Prérequis

- Windows, Python **3.12** ;
- `uv` ;
- Ollama installé et démarré ;
- un modèle Ollama disponible.

Vérifier Ollama :

```powershell
ollama list
```

Le modèle par défaut du projet est :

```text
llama3.2:latest
```

Si besoin :

```powershell
ollama pull llama3.2:latest
```

---

## 3. Installation

```powershell
cd "D:\EMSI-RelatedGeneralFiles-S9\IA generative Visuelle + Textuelle\maintidoc"
uv sync
```

---

## 4. Construire les données

### 4.1. Ingestion du PDF

```powershell
uv run python -m maintidoc.ingest
```

Résultat attendu :

```text
Pages : 9
Tableaux : 9
Images : 6
Chunks : 26
```

### 4.2. Index Qdrant local

```powershell
uv run python -m maintidoc.vector_store
```

Résultat attendu :

```text
text_points : 26
image_points : 5
```

### 4.3. OCR optionnel

```powershell
uv run python -m maintidoc.ocr
```

L’OCR n’est pas nécessaire pour le texte principal du manuel, mais il est utile
pour les PDF scannés.

---

## 5. Lancer l’application

Vérifier qu’Ollama tourne, puis :

```powershell
uv run streamlit run app.py
```

Streamlit ouvre une page locale, généralement :

```text
http://localhost:8501
```

Si le port est occupé :

```powershell
uv run streamlit run app.py --server.port 8502
```

### Version Docker

Pour lancer l’application **et les bases** :

```powershell
docker compose up -d --build
```

L’application est alors sur `http://localhost:8501`, PostgreSQL sur
`localhost:5432`, Adminer sur `http://localhost:8080` et Qdrant sur
`http://localhost:6333/dashboard`.

Voir [docker.md](docker.md).

---

## 6. Interface générale

L’application contient quatre onglets :

| Onglet | Rôle |
|---|---|
| **Search & answer** | recherche + génération sourcée |
| **LangGraph agent** | workflow agentique avec preuves |
| **MCP tickets** | historique, brouillon, approbation, ticket |
| **Corpus** | inventaire et schémas |

La barre latérale permet de choisir :

- le modèle Ollama ;
- l’activation du reranker multilingue.

---

## 7. Scénario 1 — Recherche et réponse sourcée

### Étape 1 — Poser la question

Dans l’onglet **Search & answer** :

```text
Technician question:
What does the orange AL-01 LED mean?
```

Requête visuelle :

```text
CLIP visual query:
orange warning LED storage array front panel
```

### Étape 1 bis — Photo du panneau (optionnel)

Utiliser :

```text
Panel photo (optional — JPG/PNG)
```

L’application :

1. affiche la photo ;
2. l’envoie à `qwen2.5vl:3b` ;
3. récupère une description visuelle ;
4. utilise aussi l’image comme requête CLIP.

Si le VLM n’est pas disponible, l’application continue avec CLIP seul.

La description apparaît dans **Vision model analysis of the uploaded photo**.

### Étape 2 — Cliquer sur **Search**

L’application affiche :

- les pages retenues après fusion RRF ;
- les passages et tableaux ;
- le schéma sélectionné.

Résultat attendu :

```text
page 5  — texte + visuel
page 3  — visuel
page 7  — texte
page 2  — visuel
```

Preuves attendues :

```text
P05-TEXT
P05-TAB01
P05-IMG01
```

### Étape 3 — Cliquer sur **Generate sourced answer**

L’application affiche :

- la réponse ;
- le statut ;
- le mode (`ollama` ou `fallback`) ;
- les citations ;
- les incertitudes ;
- la vérification des citations.

Exemple de réponse :

```text
The orange AL-01 LED indicates a degraded FC path on HBA1,
requiring verification of DIAG-FC-01 and FIG-02.
```

Citations :

```text
P05-TAB01 · page 5
P05-TEXT · page 5
```

### Étape 4 — Lire la vérification

```text
Citation check: all references exist in the retrieved evidence.
```

Si une citation n’existe pas dans les preuves, elle est retirée et signalée.

---

## 8. Scénario 2 — Agent LangGraph

### Étape 1 — Ouvrir **LangGraph agent**

Utiliser la même question ou une autre.

### Étape 2 — Cliquer sur **Run LangGraph agent**

L’agent exécute :

```text
retrieve → generate → validate
```

Puis il choisit :

```text
finalize  → réponse
clarify   → demande de précision
```

### Étape 3 — Lire la réponse et les preuves

L’onglet affiche :

- la réponse ;
- le statut ;
- les citations ;
- **Evidence used by the agent** ;
- les passages et tableaux ;
- la figure.

### Tester la clarification

Poser :

```text
What is the price of the SAN-LAB 2000?
```

Résultat attendu :

```text
needs_clarification
```

L’agent ne doit pas inventer un prix absent du manuel.

---

## 9. Scénario 3 — MCP et ticket

### Étape 1 — Ouvrir **MCP tickets**

Cliquer sur **Fetch history**.

L’application appelle MCP :

```text
get_equipment_history("SAN-LAB-2000")
get_open_tickets("SAN-LAB-2000")
```

Résultat attendu :

- 4 interventions (`INC-104`, `INC-117`, `INC-125`, `INC-130`) ;
- 0 ticket ouvert au départ.

### Étape 2 — Préparer un brouillon

Remplir :

```text
Title: AL-01 alert on fabric A
Description: FC path degraded on HBA1, recurrence to be checked.
```

Cliquer sur **Prepare draft**.

L’application affiche :

```text
Draft DRAFT-... — no ticket has been created yet.
```

### Étape 3 — Approuver

Cliquer sur **Approve this draft (human)**.

L’application génère :

```text
Approval token: APPROVAL-...
```

Le jeton est lié au hash du contenu.

### Étape 4 — Créer le ticket

Cliquer sur **Create ticket via MCP**.

Le serveur MCP vérifie :

- le jeton ;
- le contenu ;
- l’idempotence.

Puis il crée le ticket :

```text
TCK-XXXXXX
```

### Étape 5 — Vérifier l’idempotence

Cliquer à nouveau sur **Create ticket via MCP**.

Le même ticket est retourné :

```text
idempotent: True
```

Aucun doublon n’est créé.

### Étape 6 — Vérifier l’audit

```powershell
Get-Content data\mock\audit.jsonl | Select-Object -Last 5
```

On doit voir :

```text
get_equipment_history
prepare_ticket
approve_ticket
create_ticket
```

---

## 10. Scénario 4 — Corpus

L’onglet **Corpus** affiche :

- l’inventaire des 9 pages ;
- les 9 tableaux ;
- les 5 schémas ;
- les images extraites.

C’est la vue de contrôle du corpus.

---

## 11. Paramètres

### Modèle Ollama

Dans la barre latérale :

```text
Ollama model: llama3.2:latest
```

Pour un modèle vision :

```text
qwen2.5vl:3b
```

Mais vérifier la mémoire GPU avant :

```powershell
nvidia-smi
```

### Reranker

Case :

```text
Use multilingual reranker
```

Désactivée par défaut.

Pourquoi : sur les 14 questions du corpus, le reranker dégrade légèrement le
rappel. Il reste disponible pour expérimentation.

---

## 12. Problèmes fréquents

### `Connection refused` vers Ollama

Vérifier :

```powershell
ollama list
```

Puis démarrer Ollama si nécessaire.

### `model not found`

```powershell
ollama pull llama3.2:latest
```

### `Collection Qdrant absente`

```powershell
uv run python -m maintidoc.vector_store
```

### `ModuleNotFoundError`

```powershell
uv sync
```

### Réponse lente

- fermer les applications GPU ;
- utiliser un modèle plus petit ;
- réduire la taille du contexte.

### Réponse `fallback`

Le modèle Ollama n’a pas répondu. L’application a produit une réponse extractive
avec citation. Ce n’est pas une erreur bloquante, mais la réponse est moins fluide.

---

## 13. Ce qu’il ne faut pas faire

- Ne pas créer un ticket sans **Approve this draft**.
- Ne pas modifier le titre ou la description après approbation : le jeton devient
  invalide.
- Ne pas interpréter une similarité CLIP comme une probabilité.
- Ne pas utiliser l’application sur une baie SAN réelle.
- Ne pas oublier que le corpus est **fictif**.

---

## 14. Commandes utiles

```powershell
# Installation
uv sync

# Ingestion
uv run python -m maintidoc.ingest

# Index Qdrant
uv run python -m maintidoc.vector_store

# OCR
uv run python -m maintidoc.ocr

# Application
uv run streamlit run app.py

# Démo MCP en ligne de commande
uv run python mcp_client.py --reset

# Tests
uv run python -m pytest -q
```

---

## 15. Résumé du parcours de démonstration

```text
1. Corpus → 9 pages, 9 tableaux, 5 schémas
2. Search → pages 5, 3, 7, 2
3. Generate → réponse + P05-TAB01 page 5
4. LangGraph → answered
5. LangGraph → price → needs_clarification
6. MCP → historique
7. MCP → brouillon → approbation → ticket
8. MCP → deuxième appel → idempotent: True
9. Corpus → inventaire et figures
```
