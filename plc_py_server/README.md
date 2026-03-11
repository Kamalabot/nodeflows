# Node-RED PLC Python MCP Server (SSE)

This is a Python-based Model Context Protocol (MCP) server that exposes a Server-Sent Events (SSE) endpoint. It acts as a bridge between an AI Assistant and a local Node-RED instance, allowing the AI to fetch live simulated Modbus PLC data and PC health metrics over HTTP.

## Architecture

This project was built using the following stack:
- **[uv](https://github.com/astral-sh/uv)** - Extremely fast Python package and project manager.
- **[mcp](https://github.com/modelcontextprotocol/python-sdk)** - The official Python SDK for the Model Context Protocol.
- **[Starlette](https://www.starlette.io/) & [Uvicorn](https://www.uvicorn.org/)** - For hosting the high-performance ASGI web server.
- **[HTTPX](https://www.python-httpx.org/)** - For making asynchronous requests to the local Node-RED instance.

Unlike the default `stdio` transport used in many MCP examples, this server uses the `SseServerTransport`. This allows the server to run independently on a network port, meaning remote clients or multiple AI agents can connect to it securely via HTTP URLs (`http://<ip>:3001/sse`) without needing to spawn a local subprocess.

## Prerequisites

- [uv](https://docs.astral.sh/uv/getting-started/installation/) installed on your system.
- Node-RED running locally on port `1880` with the `/api/scada` and `/api/pc_health` endpoints configured.

## Installation

1. Navigate to the project directory:
   ```bash
   cd d:\gitFolders\nodeflows\plc_py_server
   ```

2. Install the dependencies and create the virtual environment using `uv`:
   ```bash
   uv sync
   ```
   *(Note: The dependencies — `mcp`, `httpx`, `uvicorn`, and `starlette` — are already defined in the `pyproject.toml` file.)*

## Running the Server

Start the Uvicorn ASGI server using `uv`:

```bash
uv run python server.py
```

You should see output similar to:
```
Starting Modbus Python MCP SSE Server on http://0.0.0.0:3001
SSE Endpoint: http://127.0.0.1:3001/sse
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:3001 (Press CTRL+C to quit)
```

## Connecting an AI Client

To connect an AI Assistant (like Cursor, Claude Desktop, or another MCP client) to this server over the network, you need to configure it to use the SSE endpoint.

Add the following to your AI's MCP configuration JSON:

```json
"mcpServers": {
  "nodered-plc-bridge": {
    "url": "http://127.0.0.1:3001/sse"
  }
}
```

If you are hosting this on a remote server, replace `127.0.0.1` with the server's IP address or domain name.

## Provided Tools

Once connected, the AI will have access to the following tools:

- `get_pc_health`: Returns CPU and memory layout of the host Windows machine from Node-RED (`GET http://127.0.0.1:1880/api/pc_health`).
- `get_plc_data`: Returns simulated live Modbus PLC data (sensors, counters, patterns) from Node-RED (`GET http://127.0.0.1:1880/api/scada`).

## Learnings / Troubleshooting

### 1. Missing Import — `Could not find name 'Route'`

**Error:** `Could not find name 'Route'` at `server.py:L80`.

**Cause:** `Route` was used in the routing table but only `Mount` was imported from `starlette.routing`.

**Lesson:** Always verify that every name used in a file has a corresponding import. Python will not auto-resolve names from packages — each class/function must be explicitly imported.

---

### 2. `TypeError: 'NoneType' object is not callable` on incoming requests

**Error:** After a `GET /sse` (200 OK) and `POST /sse` (202 Accepted), the server crashed with:
```
await response(scope, receive, send)
TypeError: 'NoneType' object is not callable
```

**Cause:** Starlette's `Route` wraps the endpoint and expects it to **return a `Response` object**. The `handle_mcp` endpoint was calling `transport.handle_request(scope, receive, send)` directly (a raw ASGI call) and returning `None`. Starlette then tried to execute `await None(scope, receive, send)`.

**Fix:** The MCP SDK's `StreamableHTTPServerTransport.handle_request` is itself a raw **ASGI application** (it accepts `scope, receive, send`). The correct Starlette primitive for mounting a raw ASGI app is `Mount`, not `Route`:

```python
# ❌ Broken — Route wraps the endpoint; expects a Response return value
async def handle_mcp(request):
    await transport.handle_request(request.scope, request.receive, request._send)

app = Starlette(routes=[
    Route("/sse", endpoint=handle_mcp, methods=["GET", "POST", "DELETE"]),
])

# ✅ Fixed — Mount passes ASGI calls straight through, no wrapping
app = Starlette(routes=[
    Mount("/sse", app=transport.handle_request),
])
```

**Lesson:** Understand the difference between Starlette's `Route` and `Mount`:
| | `Route` | `Mount` |
|---|---|---|
| **Input** | Starlette endpoint `(request) → Response` | Raw ASGI app `(scope, receive, send)` |
| **Use when** | Writing standard request/response handlers | Mounting sub-applications or ASGI middleware |
| **Wrapping** | Wraps your function, expects a `Response` return | No wrapping — passes ASGI protocol directly |
