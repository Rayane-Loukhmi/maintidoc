"""Serveur MCP MaintiDoc : historique, tickets ouverts, création contrôlée."""
from __future__ import annotations

from mcp.server.mcpserver import MCPServer

from .mcp_store import (
    create_ticket as store_create_ticket,
    get_equipment_history as store_get_history,
    get_open_tickets as store_get_open_tickets,
)

mcp = MCPServer(
    name="MaintiDoc SAN",
    instructions=(
        "Serveur documentaire MaintiDoc. Les outils lisent un historique fictif "
        "et créent un ticket uniquement avec un jeton d'approbation humaine."
    ),
)


@mcp.tool()
def get_equipment_history(equipment_id: str) -> dict:
    """Retourne l'historique des interventions d'un équipement SAN."""
    return store_get_history(equipment_id)


@mcp.tool()
def get_open_tickets(equipment_id: str) -> dict:
    """Retourne les tickets ouverts d'un équipement SAN."""
    return store_get_open_tickets(equipment_id)


@mcp.tool()
def create_ticket(equipment_id: str, title: str, description: str,
                  approval_token: str, idempotency_key: str | None = None) -> dict:
    """Crée un ticket après vérification du jeton d'approbation humaine.

    Le jeton est lié au contenu exact (équipement, titre, description).
    """
    return store_create_ticket(
        equipment_id=equipment_id,
        title=title,
        description=description,
        approval_token=approval_token,
        idempotency_key=idempotency_key,
    )


if __name__ == "__main__":
    mcp.run()
