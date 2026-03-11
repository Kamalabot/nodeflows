# Transitioning MCP Server from stdio to HTTP/SSE

**Goal:** Modify the existing

index.js Node.js script to run as an Express web server using `SSEServerTransport`. This allows the AI agent/client to connect over the network using HTTP instead of requiring the script to be spawned locally via `stdio`.

## Proposed Changes

### `d:\gitFolders\nodeflows\mcp_server\package.json`

* We need to add `express` and `cors` as dependencies to serve the HTTP endpoints.

…\nodeflows\mcp_server\index.js

* **[MODIFY] index.js(file:///d:/gitFolders/nodeflows/mcp_server/index.js)** :
* Switch transport from `StdioServerTransport` to `SSEServerTransport`.
* Create an Express app with basic CORS and JSON body-parsing.
* Expose a `GET /sse` endpoint that establishes the persistent server-sent events connection.
* Expose a `POST /messages` endpoint that handles incoming JSON-RPC calls from the client and routes them to the SSE transport.
* Set the server to listen on a configurable port (e.g., 3001).
* Define clear routing so an external client knows where to connect.

## Verification Plan

### Automated/Local Tests

* **Start the Server:** Ensure the command `node index.js` runs without crashing and correctly logs that it is listening on port 3001.
* **SSE Connection Check:** Send a `curl` request to `http://localhost:3001/sse` and verify it returns `Content-Type: text/event-stream` and issues an `endpoint` URL event.
* **Client Configuration:** Provide the user with the exact configuration block required for their AI IDE (e.g., Cursor, Claude Desktop) to connect to an MCP `sse` endpoint rather than `command`.

### Manual Testing

* The user will update their AI settings to use the SSE URL (e.g., `http://localhost:3001/sse`).
* Ask the AI to invoke the `get_plc_data` tool to verify network-level execution.
