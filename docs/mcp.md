# MCP, tickets et validation humaine

Ce document décrit `src/maintidoc/mcp_server.py`, `src/maintidoc/mcp_store.py`
et `src/maintidoc/mcp_calls.py`.

## 1. Pourquoi MCP

MCP (*Model Context Protocol*) est un protocole client-serveur. Le serveur
expose des **outils typés** ; le client les appelle.

Le modèle ne reçoit pas les identifiants de la base. Il voit seulement :

- le nom de l’outil ;
- sa description ;
- son schéma d’entrée.

Le serveur applique les règles de sécurité.

## 2. Les trois outils

### `get_equipment_history(equipment_id)`

Retourne les interventions fictives d’un équipement.

### `get_open_tickets(equipment_id)`

Retourne les tickets ouverts.

### `create_ticket(equipment_id, title, description, approval_token, idempotency_key)`

Crée un ticket **uniquement** si :

- le jeton existe ;
- le contenu correspond au hash approuvé ;
- la clé d’idempotence n’a pas déjà été utilisée.

## 3. `mcp_store.py`

### `prepare_ticket(equipment_id, title, description)`

Crée un brouillon :

```python
{
    "draft_id": "DRAFT-...",
    "content": {...},
    "content_hash": "...",
    "status": "pending",
}
```

Aucune création externe n’a lieu.

### `approve_ticket(draft_id, approver=...)`

Simule l’approbation humaine et génère :

```text
APPROVAL-...
```

Le jeton est stocké avec :

- `draft_id` ;
- `content_hash` ;
- `approver` ;
- `approved_at`.

### `create_ticket(...)`

Vérifie :

1. l’existence du jeton ;
2. le hash du contenu ;
3. l’idempotence.

Puis écrit le ticket et l’audit.

### `reset_mock()`

Réinitialise tickets, brouillons, approbations et audit.

## 4. Pourquoi le hash du contenu

Le jeton est lié à :

```python
hash(equipment_id, title, description)
```

Si l’utilisateur modifie le titre ou la description après l’approbation, le hash
change et le serveur refuse.

C’est la différence entre :

```text
« approuver un ticket »
```

et

```text
« approuver un contenu exact »
```

## 5. Idempotence

Le client envoie :

```text
idempotency_key = "demo-al01-001"
```

Si un ticket existe déjà avec cette clé, le serveur retourne le même ticket avec
`idempotent: True`.

Pourquoi : éviter les doublons en cas de retry réseau.

## 6. Audit

Chaque appel écrit dans `data/mock/audit.jsonl` :

```json
{"at": "...", "action": "create_ticket", "ticket_id": "TCK-...", "approved_by": "..."}
```

Actions tracées :

- `get_equipment_history` ;
- `get_open_tickets` ;
- `prepare_ticket` ;
- `approve_ticket` ;
- `create_ticket`.

## 7. `mcp_calls.py`

Fournit des appels synchrones pour Streamlit et les notebooks :

```python
call_tool("get_equipment_history", {"equipment_id": "SAN-LAB-2000"})
list_tools()
```

Il lance le serveur en sous-processus stdio et ferme proprement la session.

## 8. Séquence complète

```text
Technicien → Application
Application → prepare_ticket (brouillon)
Application → humain (affichage du contenu)
Humain → approve_ticket (jeton)
Application → MCP create_ticket(token)
Serveur → vérifie token + hash
Serveur → écrit ticket + audit
Serveur → retourne ticket
```

## 9. Limites

- Données mock, pas de vraie base.
- Pas d’authentification ni de RBAC.
- L’approbation est simulée par `approve_ticket()`.
- L’idempotence est locale.
- Pas de LangGraph `interrupt()` pour l’approbation.
- Pas de chiffrement des jetons.

## 10. Ce qu’il faut retenir

- Le serveur applique les règles, pas le modèle.
- Le jeton est lié au contenu.
- L’idempotence évite les doublons.
- L’audit rend les actions traçables.
- Aucune création sans approbation humaine.
