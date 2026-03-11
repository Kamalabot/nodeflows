"""
Shared tool configuration — loaded once from tools.json.

Provides:
    TOOL_DEFS      – raw list of tool dicts from JSON
    TOOL_URL_MAP   – {name: url} lookup
    execute_tool() – async helper to GET a Node-RED endpoint by tool name
"""

import json
import httpx
from pathlib import Path

# ── Load tool definitions from JSON ──────────────────────────────────
TOOLS_FILE = Path(__file__).parent / "tools.json"

with open(TOOLS_FILE, "r") as f:
    TOOL_DEFS: list[dict] = json.load(f)

# Quick lookup: tool_name → url
TOOL_URL_MAP: dict[str, str] = {t["name"]: t["url"] for t in TOOL_DEFS}


async def execute_tool(name: str) -> str:
    """Call a Node-RED endpoint by tool name and return the response text."""
    url = TOOL_URL_MAP.get(name)
    if url is None:
        return json.dumps({"error": f"Tool not found: {name}"})

    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        return resp.text
