import anyio
import httpx
import uvicorn
from uuid import uuid4
from contextlib import asynccontextmanager

from starlette.applications import Starlette
from starlette.routing import Mount

from mcp.server import Server
from mcp.server.streamable_http import StreamableHTTPServerTransport
from mcp.types import Tool, TextContent

# Initialize the MCP Server
mcp = Server("nodered-bridge-py")

@mcp.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="get_pc_health",
            description="Returns CPU and memory layout of the host Windows machine from Node-RED.",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="get_plc_data",
            description="Returns simulated live Modbus PLC data (sensors, counters, patterns) from Node-RED.",
            inputSchema={"type": "object", "properties": {}}
        )
    ]

@mcp.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    async with httpx.AsyncClient() as client:
        if name == "get_pc_health":
            response = await client.get("http://127.0.0.1:1880/api/pc_health")
            return [TextContent(type="text", text=str(response.text))]
        elif name == "get_plc_data":
            response = await client.get("http://127.0.0.1:1880/api/scada")
            return [TextContent(type="text", text=response.text)]
        else:
            raise ValueError(f"Tool not found: {name}")

# Global transport - stays connected for the lifetime of the app
transport = StreamableHTTPServerTransport(
    mcp_session_id=uuid4().hex,
)

# Background task group for running the MCP server
_task_group = None
_streams = None

@asynccontextmanager
async def lifespan(app):
    """
    App lifespan: connect the transport once at startup,
    run the MCP server in the background, and clean up on shutdown.
    """
    async with transport.connect() as (read_stream, write_stream):
        async with anyio.create_task_group() as tg:
            async def run_mcp_server():
                await mcp.run(read_stream, write_stream, mcp.create_initialization_options())

            tg.start_soon(run_mcp_server)
            yield
            tg.cancel_scope.cancel()


# Bind the handler to a Starlette ASGI app
# Mount the transport's ASGI handler directly (it handles scope/receive/send natively)
app = Starlette(debug=True, routes=[
    Mount("/sse", app=transport.handle_request),
], lifespan=lifespan)

if __name__ == "__main__":
    print("Starting Modbus Python MCP Streamable HTTP Server on http://0.0.0.0:3001")
    print("MCP Endpoint: http://127.0.0.1:3001/sse")
    uvicorn.run(app, host="0.0.0.0", port=3001)
