# Docker — lancer MaintiDoc et ouvrir la base de données

Ce document décrit l’environnement Docker Compose du projet.

## 1. Ce que Docker lance

```text
docker compose up -d --build
```

| Service | Rôle | Adresse locale |
|---|---|---|
| `app` | Streamlit + RAG + MCP | http://localhost:8501 |
| `qdrant` | base vectorielle | http://localhost:6333/dashboard |
| `postgres` | base relationnelle | `localhost:5432` |
| `adminer` | interface web PostgreSQL | http://localhost:8080 |
| `minio` | stockage objet S3 | http://localhost:9000 |
| `mlflow` | suivi d’expériences (profil `mlops`) | http://localhost:5000 |

Ollama reste **natif sur Windows** : le conteneur `app` l’appelle via
`http://host.docker.internal:11434`.

> **État actuel :** Qdrant est réellement utilisé par l’application. PostgreSQL
> et MinIO sont provisionnés pour l’architecture cible ; le serveur MCP utilise
> encore ses fichiers JSON mock (`data/mock/`). La migration MCP vers PostgreSQL
> est l’étape suivante.

---

## 2. Prérequis

- Docker Desktop démarré ;
- backend WSL2 ;
- Ollama démarré sur Windows ;
- le modèle Ollama disponible :

```powershell
ollama list
```

Le modèle par défaut est `llama3.2:latest`.

---

## 3. Lancer la stack

Depuis la racine du projet :

```powershell
cd "D:\EMSI-RelatedGeneralFiles-S9\IA generative Visuelle + Textuelle\maintidoc"
docker compose up -d --build
```

Le premier build peut prendre plusieurs minutes : il installe PyTorch,
sentence-transformers, Qdrant, etc.

Vérifier :

```powershell
docker compose ps
```

Suivre les logs de l’application :

```powershell
docker compose logs -f app
```

---

## 4. Ouvrir la base PostgreSQL

### Option A — Adminer, interface web

Ouvrir :

```text
http://localhost:8080
```

Remplir :

```text
Système   : PostgreSQL
Serveur   : postgres
Utilisateur : maintidoc
Mot de passe : maintidoc_dev
Base      : maintidoc
```

Cliquer sur **Login**.

Tu peux alors :

- voir les tables ;
- exécuter des requêtes SQL ;
- consulter `maintenance_history`, `tickets`, `approvals`, `audit_log`.

### Option B — psql dans le conteneur

```powershell
docker compose exec postgres psql -U maintidoc -d maintidoc
```

Puis :

```sql
\dt
SELECT * FROM documents;
SELECT * FROM maintenance_history;
SELECT * FROM tickets;
SELECT * FROM audit_log ORDER BY created_at DESC LIMIT 10;
```

Quitter :

```sql
\q
```

### Option C — connexion externe

Depuis un client SQL (DBeaver, DataGrip, psql) :

```text
Host     : localhost
Port     : 5432
Database : maintidoc
User     : maintidoc
Password : maintidoc_dev
```

---

## 5. Qdrant

Dashboard :

```text
http://localhost:6333/dashboard
```

API :

```text
http://localhost:6333
```

Collections :

```text
maintidoc_text
maintidoc_images
```

Le service `app` exécute `python -m maintidoc.bootstrap` au démarrage : si les
collections n’existent pas, elles sont construites depuis les embeddings locaux.

---

## 6. MinIO

MinIO expose une API S3 sur :

```text
http://localhost:9000
```

Identifiants par défaut :

```text
User     : maintidoc
Password : maintidoc_dev
```

Le bucket `maintidoc` est créé automatiquement.

L’image Bitnami utilisée ne fournit pas la console web MinIO ; elle expose
uniquement l’API S3. Le stockage des fichiers n’est pas encore branché dans
l’application ; il est fourni pour l’architecture cible.

---

## 7. Ollama

Ollama n’est pas dans Docker. Il tourne sur Windows et le conteneur l’appelle via
`host.docker.internal`.

Important : Ollama doit écouter sur `0.0.0.0:11434`, pas seulement sur
`127.0.0.1`. Sinon le conteneur ne peut pas l’atteindre.

```powershell
$env:OLLAMA_HOST = "0.0.0.0:11434"
ollama serve
```

Vérifier depuis le conteneur :

```powershell
docker compose exec app python -c "import os; print(os.environ['OLLAMA_HOST'])"
```

Si Ollama n’est pas démarré, l’application utilise le fallback extractif.

---

## 8. MLflow (optionnel)

```powershell
docker compose --profile mlops up -d
```

Interface :

```text
http://localhost:5000
```

---

## 9. Arrêter

```powershell
docker compose down
```

Conserver les volumes :

```text
Qdrant, PostgreSQL, MinIO et MLflow gardent leurs données.
```

Réinitialiser complètement :

```powershell
docker compose down -v
```

Attention : `-v` supprime les volumes, donc la base PostgreSQL, les collections
Qdrant et les fichiers MinIO.

---

## 10. Commandes utiles

```powershell
# Voir les conteneurs
docker compose ps

# Logs de l'application
docker compose logs -f app

# Redémarrer l'application
docker compose restart app

# Reconstruire l'image
docker compose build app

# Shell dans l'application
docker compose exec app bash

# PostgreSQL
docker compose exec postgres psql -U maintidoc -d maintidoc

# Qdrant
curl http://localhost:6333/collections

# MinIO
docker compose logs minio
```

---

## 11. Dépannage

### `port is already allocated`

Un service local utilise déjà le port. Changer le port dans
`docker-compose.yml`, par exemple :

```yaml
ports:
  - "8502:8501"
```

### `Cannot connect to the Docker daemon`

Démarrer Docker Desktop.

### `postgres` ne démarre pas

```powershell
docker compose logs postgres
```

Si le volume a été initialisé avec un ancien schéma :

```powershell
docker compose down -v
docker compose up -d --build
```

### L’application ne voit pas Ollama

Vérifier :

```powershell
ollama list
docker compose exec app python -c "import requests; print(requests.get('http://host.docker.internal:11434/api/tags').status_code)"
```

### Qdrant vide

```powershell
docker compose logs app | Select-String "Qdrant"
```

Puis relancer :

```powershell
docker compose restart app
```

---

## 12. Sécurité

Les identifiants sont des valeurs de **développement** :

```text
maintidoc / maintidoc_dev
```

Ne pas les utiliser en production. Pour un déploiement réel :

- secrets Docker ou variables d’environnement protégées ;
- mot de passe PostgreSQL fort ;
- MinIO avec accès restreint ;
- réseau privé ;
- TLS ;
- sauvegardes.
