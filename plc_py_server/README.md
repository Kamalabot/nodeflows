# Node-RED PLC Python MCP Server

A Python-based Model Context Protocol (MCP) server that bridges AI Assistants to a local Node-RED instance, exposing live simulated Modbus PLC data and PC health metrics. It also offers a built-in `/chat` endpoint for direct LLM-powered Q&A with tool access.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  server_rd_json.py  (Starlette + Uvicorn, port 3001)           │
│                                                                 │
│  ┌──────────────────────────────┐  ┌──────────────────────────┐ │
│  │  PART 1 — Tool Layer         │  │  PART 2 — Model Layer    │ │
│  │  Mount("/sse")               │  │  Route("/chat")          │ │
│  │                              │  │                          │ │
│  │  MCP protocol over           │  │  POST { prompt }         │ │
│  │  Streamable HTTP             │  │    → LM Studio (LLM)     │ │
│  │  External AI clients         │  │    → tool-call loop      │ │
│  │  (Cursor, Claude, etc.)      │  │    → JSON response       │ │
│  └──────────┬───────────────────┘  └──────────┬───────────────┘ │
│             │                                  │                │
│             ▼                                  ▼                │
│       tools.json  ──────────►  Node-RED (localhost:1880)        │
│       (name, desc, url)        /api/pc_health, /api/scada      │
└─────────────────────────────────────────────────────────────────┘
```

### Stack

- **[uv](https://github.com/astral-sh/uv)** — Fast Python package manager
- **[mcp](https://github.com/modelcontextprotocol/python-sdk)** — Official MCP Python SDK
- **[Starlette](https://www.starlette.io/) & [Uvicorn](https://www.uvicorn.org/)** — ASGI web server
- **[HTTPX](https://www.python-httpx.org/)** — Async HTTP client for Node-RED calls
- **[OpenAI SDK](https://github.com/openai/openai-python)** — LM Studio API calls (OpenAI-compatible)

## Prerequisites

- [uv](https://docs.astral.sh/uv/getting-started/installation/) installed
- Node-RED running on port `1880` with `/api/scada` and `/api/pc_health` endpoints
- (For `/chat`) LM Studio running on port `1234` with a model loaded

## Installation

```bash
cd d:\gitFolders\nodeflows\plc_py_server
uv sync
```

---

# Part 1 — Tool Layer (MCP)

This is the core MCP server. External AI clients connect here via the Streamable HTTP transport.

## Server Variants

| File | Description |
| --- | --- |
| `server.py` | Hardcoded tool definitions — simple, no external config |
| `server_rd_json.py` | Reads tools from `tools.json` + includes `/chat` endpoint |

## Running

```bash
# Hardcoded variant
uv run python server.py

# JSON-driven variant (recommended)
uv run python server_rd_json.py
```

## Connecting an AI Client

Add to your MCP configuration JSON:

```json
"mcpServers": {
  "nodered-plc-bridge": {
    "url": "http://127.0.0.1:3001/sse"
  }
}
```

## Provided Tools

| Tool | Endpoint | Description |
| --- | --- | --- |
| `get_pc_health` | `GET http://127.0.0.1:1880/api/pc_health` | CPU and memory metrics |
| `get_plc_data` | `GET http://127.0.0.1:1880/api/scada` | Simulated Modbus PLC data |

## `tools.json` Schema

```json
[
  {
    "name": "get_pc_health",
    "description": "Returns CPU and memory layout of the host Windows machine.",
    "url": "http://127.0.0.1:1880/api/pc_health"
  }
]
```

| Field | Description |
| --- | --- |
| `name` | Unique tool name exposed to AI clients |
| `description` | Human-readable description shown in tool listings |
| `url` | HTTP GET endpoint called when the tool is invoked |

To add a new tool, append an entry to `tools.json` and restart — no code changes needed.

---

# Part 2 — Model Layer (`/chat` Endpoint)

A standalone HTTP endpoint that accepts a user prompt, calls LM Studio, lets the model use the tools, and returns the final answer. No MCP client needed — any HTTP client (curl, browser, frontend app) can use it.

## How It Works

```
Client                    Server                     LM Studio          Node-RED
  │                         │                            │                  │
  │  POST /chat             │                            │                  │
  │  { "prompt": "..." }    │                            │                  │
  │────────────────────────►│                            │                  │
  │                         │  messages + tools           │                  │
  │                         │───────────────────────────►│                  │
  │                         │  tool_call: get_pc_health   │                  │
  │                         │◄───────────────────────────│                  │
  │                         │                            │  GET /api/...    │
  │                         │───────────────────────────────────────────────►│
  │                         │                            │  { cpu: 42% }    │
  │                         │◄───────────────────────────────────────────────│
  │                         │  tool result → messages     │                  │
  │                         │───────────────────────────►│                  │
  │                         │  final text answer          │                  │
  │                         │◄───────────────────────────│                  │
  │  { "response": "..." }  │                            │                  │
  │◄────────────────────────│                            │                  │
```

1. Client sends `POST /chat` with a prompt
2. Server forwards the prompt + tool definitions to LM Studio
3. If the model requests tool calls, the server executes them against Node-RED
4. Tool results are fed back to the model
5. Steps 3–4 repeat (up to 5 rounds) until the model gives a final text answer
6. The JSON response is returned to the client

## Configuration

Edit these constants at the top of `server_rd_json.py`:

```python
LM_STUDIO_BASE_URL = "http://localhost:1234/v1"
LM_STUDIO_MODEL = "qwen2.5-7b-instruct"   # ← change to your loaded model
MAX_TOOL_ROUNDS = 5
```

## Usage

```bash
curl -X POST http://127.0.0.1:3001/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is the current CPU usage?"}'
```

Response:

```json
{
  "response": "The current CPU usage is 42%. Memory is at 8.2 GB / 16 GB.",
  "tool_calls_made": [
    { "tool": "get_pc_health", "result_preview": "{\"cpu\": 42, ...}" }
  ]
}
```

---

# Streamable HTTP & the `/chat` Endpoint

> [!IMPORTANT]
> **Short answer: No, Streamable HTTP does NOT create any challenge for the `/chat` model call.**

The two endpoints are **completely independent** even though they live in the same Starlette app:

| | `/sse` (MCP) | `/chat` (Model) |
| --- | --- | --- |
| **Starlette primitive** | `Mount` (raw ASGI) | `Route` (request → response) |
| **Protocol** | MCP over Streamable HTTP | Plain REST (JSON in, JSON out) |
| **Transport** | `StreamableHTTPServerTransport` | Not involved at all |
| **Who calls tools?** | External AI client decides | LM Studio decides (server executes) |

### Why there's no conflict

```python
app = Starlette(routes=[
    Mount("/sse", app=transport.handle_request),   # MCP — raw ASGI passthrough
    Route("/chat", endpoint=chat_endpoint, ...),   # REST — normal request/response
])
```

- **`/sse`** is mounted as a raw ASGI app via `Mount`. The `StreamableHTTPServerTransport` owns this path entirely — it handles the MCP protocol, sessions, and streaming.
- **`/chat`** is a standard Starlette `Route`. It receives a `Request`, returns a `JSONResponse`. It has **zero interaction** with the MCP transport.

The `/chat` endpoint calls the Node-RED URLs directly (via `TOOL_URL_MAP`), completely bypassing the MCP transport. It reuses the same `tools.json` config but shares no state or protocol machinery with MCP.

### When it WOULD be a problem

If you wanted `/chat` to call tools **through** the MCP protocol (i.e., acting as an MCP client to your own MCP server), that would be complex — you'd need to establish an MCP session, handle streaming, etc. But since the `/chat` endpoint calls Node-RED directly, this is entirely avoided.

---

# Learnings / Troubleshooting

### 1. Missing Import — `Could not find name 'Route'`

**Error:** `Could not find name 'Route'` at `server.py:L80`.

**Cause:** `Route` was used in the routing table but only `Mount` was imported from `starlette.routing`.

**Lesson:** Always verify that every name used in a file has a corresponding import.

---

### 2. `TypeError: 'NoneType' object is not callable` on incoming requests

**Error:** Server crashed with `TypeError: 'NoneType' object is not callable` after receiving requests.

**Cause:** Starlette's `Route` wraps the endpoint and expects it to **return a `Response` object**. The endpoint was calling `transport.handle_request(scope, receive, send)` directly (a raw ASGI call) and returning `None`.

**Fix:** Use `Mount` for raw ASGI apps, `Route` for request→response endpoints:

```python
# ❌ Broken — Route expects a Response return
Route("/sse", endpoint=handle_mcp, methods=["GET", "POST", "DELETE"])

# ✅ Fixed — Mount passes ASGI calls directly
Mount("/sse", app=transport.handle_request)
```

**Lesson:** `Route` = Starlette endpoint `(request) → Response`. `Mount` = raw ASGI app `(scope, receive, send)`.
