"""
MCP + Chat Server — Thin Entrypoint

Wires together:
    Part 1 (mcp_tools)  → Mount("/sse")  — MCP Streamable HTTP for AI clients
    Part 2 (model_chat) → Route("/chat") — LM Studio agentic endpoint
"""

import anyio
import uvicorn
from uuid import uuid4
from contextlib import asynccontextmanager

from starlette.applications import Starlette
from starlette.routing import Mount, Route

from mcp.server.streamable_http import StreamableHTTPServerTransport

from tools_config import TOOL_DEFS, TOOLS_FILE
from mcp_tools import mcp
from model_chat import chat_endpoint, LM_STUDIO_MODEL, LM_STUDIO_BASE_URL

# from starlette.middleware.cors import CORSMiddleware
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


# ── Starlette App ────────────────────────────────────────────────────
app = Starlette(
    debug=True,
    routes=[
        Mount("/sse", app=transport.handle_request),      # Part 1: MCP
        Route("/chat", endpoint=chat_endpoint, methods=["POST"]),  # Part 2: Model
    ],
    lifespan=lifespan,
)

# Add CORS Middleware HERE
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"], 
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# ── Startup banner ───────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"Loaded {len(TOOL_DEFS)} tool(s) from {TOOLS_FILE.name}:")
    for t in TOOL_DEFS:
        print(f"  - {t['name']}  ->  {t['url']}")
    print()
    print(f"LM Studio model : {LM_STUDIO_MODEL}")
    print(f"LM Studio API   : {LM_STUDIO_BASE_URL}")
    print()
    print("Starting MCP Streamable HTTP Server on http://0.0.0.0:3002")
    print("  MCP Endpoint : http://127.0.0.1:3002/sse")
    print("  Chat Endpoint: http://127.0.0.1:3002/chat  (POST)")
    uvicorn.run(app, host="0.0.0.0", port=3001)
