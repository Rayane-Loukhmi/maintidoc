"""Appels MCP synchrones utilisés par Streamlit et les notebooks."""
from __future__ import annotations

import asyncio
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


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


async def _with_session(action):
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "maintidoc.mcp_server"],
    )
    with open(os.devnull, "w") as errlog:
        async with stdio_client(params, errlog=errlog) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                return await action(session)


def _run(coro):
    """Exécute une coroutine même si une boucle asyncio tourne déjà (Jupyter)."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    with ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(lambda: asyncio.run(coro)).result()


def call_tool(name: str, arguments: dict):
    async def action(session):
        result = await session.call_tool(name, arguments)
        return _payload(result)

    return _run(_with_session(action))


def list_tools() -> list[dict]:
    async def action(session):
        result = await session.list_tools()
        return [{"name": tool.name, "description": tool.description}
                for tool in result.tools]

    return _run(_with_session(action))
