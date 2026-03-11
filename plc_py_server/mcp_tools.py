"""
Part 1 — Tool Layer (MCP)

MCP server instance and tool handlers.
Reads tool definitions from tools_config and exposes them over MCP.
"""

from mcp.server import Server
from mcp.types import Tool, TextContent

from tools_config import TOOL_DEFS, TOOL_URL_MAP, execute_tool

# ── MCP Server instance ─────────────────────────────────────────────
mcp = Server("nodered-bridge-py")


@mcp.list_tools()
async def list_tools() -> list[Tool]:
    """Dynamically build the MCP tool list from the loaded JSON."""
    return [
        Tool(
            name=t["name"],
            description=t["description"],
            inputSchema={"type": "object", "properties": {}},
        )
        for t in TOOL_DEFS
    ]


@mcp.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Route the MCP tool call to the URL defined in the JSON config."""
    url = TOOL_URL_MAP.get(name)
    if url is None:
        raise ValueError(f"Tool not found: {name}")

    result = await execute_tool(name)
    return [TextContent(type="text", text=result)]
