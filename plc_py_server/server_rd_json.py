import json
import anyio
import httpx
import uvicorn
from pathlib import Path
from uuid import uuid4
from contextlib import asynccontextmanager

from starlette.applications import Starlette
from starlette.routing import Mount

from mcp.server import Server
from mcp.server.streamable_http import StreamableHTTPServerTransport
from mcp.types import Tool, TextContent

# ── Load tool definitions from JSON ──────────────────────────────────
TOOLS_FILE = Path(__file__).parent / "tools.json"

with open(TOOLS_FILE, "r") as f:
    TOOL_DEFS = json.load(f)

# Build a quick lookup: tool_name → url
TOOL_URL_MAP = {t["name"]: t["url"] for t in TOOL_DEFS}

# ── Initialize the MCP Server ────────────────────────────────────────
mcp = Server("nodered-bridge-py")


@mcp.list_tools()
async def list_tools() -> list[Tool]:
    """Dynamically build the tool list from the loaded JSON."""
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
    """Route the tool call to the URL defined in the JSON config."""
    url = TOOL_URL_MAP.get(name)
    if url is None:
        raise ValueError(f"Tool not found: {name}")

    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return [TextContent(type="text", text=response.text)]


# ── ASGI / Transport wiring ──────────────────────────────────────────
transport = StreamableHTTPServerTransport(
    mcp_session_id=uuid4().hex,
)


@asynccontextmanager
async def lifespan(app):
    """
    App lifespan: connect the transport once at startup,
    run the MCP server in the background, and clean up on shutdown.
    """
    async with transport.connect() as (read_stream, write_stream):
        async with anyio.create_task_group() as tg:
            async def run_mcp_server():
                await mcp.run(
                    read_stream, write_stream, mcp.create_initialization_options()
                )

            tg.start_soon(run_mcp_server)
            yield
            tg.cancel_scope.cancel()


app = Starlette(
    debug=True,
    routes=[Mount("/sse", app=transport.handle_request)],
    lifespan=lifespan,
)

if __name__ == "__main__":
    print(f"Loaded {len(TOOL_DEFS)} tool(s) from {TOOLS_FILE.name}:")
    for t in TOOL_DEFS:
        print(f"  • {t['name']}  →  {t['url']}")
    print()
    print("Starting MCP Streamable HTTP Server on http://0.0.0.0:3001")
    print("MCP Endpoint: http://127.0.0.1:3001/sse")
    uvicorn.run(app, host="0.0.0.0", port=3001)
