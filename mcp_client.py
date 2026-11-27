"""Client MCP de démonstration : liste les outils et exécute le flux complet."""
from __future__ import annotations

import argparse
import asyncio
import json
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from maintidoc.mcp_store import approve_ticket, prepare_ticket, reset_mock


def _payload(result):
    if getattr(result, "structured_content", None) is not None:
        return result.structured_content
    if getattr(result, "content", None):
        text = result.content[0].text
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return text
    return None


async def demo(reset: bool = False) -> None:
    if reset:
        print("Réinitialisation :", reset_mock())

    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "maintidoc.mcp_server"],
    )

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            print("\nOutils exposés :")
            for tool in tools.tools:
                print(f"- {tool.name}: {tool.description}")

            history = await session.call_tool(
                "get_equipment_history", {"equipment_id": "SAN-LAB-2000"}
            )
            print("\nHistorique :")
            print(json.dumps(_payload(history), ensure_ascii=False, indent=2))

            tickets = await session.call_tool(
                "get_open_tickets", {"equipment_id": "SAN-LAB-2000"}
            )
            print("\nTickets ouverts :")
            print(json.dumps(_payload(tickets), ensure_ascii=False, indent=2))

            draft = prepare_ticket(
                equipment_id="SAN-LAB-2000",
                title="Alerte AL-01 sur fabric A",
                description="Chemin FC dégradé sur HBA1, récurrence à vérifier.",
            )["draft"]
            approval = approve_ticket(draft["draft_id"])
            print("\nApprobation humaine :")
            print(json.dumps(approval, ensure_ascii=False, indent=2))

            created = await session.call_tool(
                "create_ticket",
                {
                    "equipment_id": "SAN-LAB-2000",
                    "title": "Alerte AL-01 sur fabric A",
                    "description": "Chemin FC dégradé sur HBA1, récurrence à vérifier.",
                    "approval_token": approval["approval_token"],
                    "idempotency_key": "demo-al01-001",
                },
            )
            print("\nCréation :")
            print(json.dumps(_payload(created), ensure_ascii=False, indent=2))

            again = await session.call_tool(
                "create_ticket",
                {
                    "equipment_id": "SAN-LAB-2000",
                    "title": "Alerte AL-01 sur fabric A",
                    "description": "Chemin FC dégradé sur HBA1, récurrence à vérifier.",
                    "approval_token": approval["approval_token"],
                    "idempotency_key": "demo-al01-001",
                },
            )
            print("\nDeuxième appel (idempotence) :")
            print(json.dumps(_payload(again), ensure_ascii=False, indent=2))

            denied = await session.call_tool(
                "create_ticket",
                {
                    "equipment_id": "SAN-LAB-2000",
                    "title": "Sans approbation",
                    "description": "Ne doit pas être créé.",
                    "approval_token": "INVALID",
                },
            )
            print("\nRefus sans jeton valide :")
            print(json.dumps(_payload(denied), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="Réinitialiser les données mock")
    args = parser.parse_args()
    asyncio.run(demo(reset=args.reset))
