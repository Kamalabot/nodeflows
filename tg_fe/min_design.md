# Minimal HTML/CSS/JS MCP Frontend (MVP)

Yes, you can absolutely build a functional MVP using pure HTML, Vanilla CSS, and basic JavaScript. This approach drops the complexity of React/Next.js and build steps, resulting in just three static files: `index.html`, `style.css`, and `app.js`.

However, to mimic an MCP Client (like Antigravity) directly from a browser, there are a few browser-specific hurdles we must handle.

## 1. The Browser Challenges (and Solutions)

| Challenge | Why it's a problem in static HTML | The MVP Workaround |
| --- | --- | --- |
| **Reading local `mcp.json`** | Browsers cannot read `C:\...\mcp.json` securely from the filesystem without user action. | Serve the folder with a simple local web server (e.g., `python -m http.server` or VS Code Live Server). The JS can then `fetch('mcp.json')`. |
| **Connecting to `/sse`** | Official MCP SDKs are built for Node.js/TypeScript and need bundlers (Vite/Webpack/Rollup). | We write a custom, lightweight Vanilla JS MCP client that uses native `EventSource` (for receiving) and `fetch` (for sending JSON-RPC messages to the server's POST endpoint). |
| **CORS (Cross-Origin)** | The web server serving `index.html` (e.g., port 8000) is different from the Python MCP server (port 3002). | The Python server must explicitly allow CORS for requests coming from the HTML frontend (update Starlette in `server_rd_json.py` to use `CORSMiddleware`). |

## 2. Architecture of the MVP

```mermaid
graph TD
    subgraph Browser Frontend (Vanilla JS)
        UI[index.html + style.css]
        AppJS[app.js]
    end

    AppJS --> |1. fetch('mcp.json')| LocalServer[Local HTTP Server<br/>Serving static files]
    AppJS <--> |2. EventSource (GET) & fetch (POST)| SSE[Python MCP Server<br/>:3002/sse]
    AppJS <--> |3. OpenAI API calls| LLM[LM Studio API<br/>:1234/v1]
```

In this setup, the **JavaScript acts as the orchestrator** (the brain). It talks to the MCP Server for tools, talks directly to LM Studio for LLM logic, and handles the chat UI updates itself.

*(Alternatively, if we just want a chat UI, it could bypass the SSE connection entirely and simply POST to the Python server's `http://127.0.0.1:3002/chat` endpoint, letting Python be the brain. But to truly act like an MCP client, the JS must do the orchestration.)*

## 3. The Telegram-like UI Implementation

**1. `index.html` Structure:**
- A main container holding a `<aside>` (Sidebar) and `<main>` (Chat Window).
- **Sidebar**: Parses `mcp.json` and lists the active Servers (e.g., `nodered-plc-bridge`) and dynamically populated tools (e.g., `get_pc_health`).
- **Chat Window**:
  - `div.messages` for the chat history, styled like Telegram bubbles (right-aligned green for user, left-aligned white for bot).
  - `div.input-area` with a textarea and a Send button.

**2. `style.css` Aesthetics:**
- Background patterns (like Telegram's chat wallpaper).
- Flexbox for the split-pane layout and input pinning at the bottom.
- Smooth transitions for new messages.

**3. `app.js` Logic:**
- **Step 1:** Run `fetch('mcp.json')`. Extract the `url` for the server (e.g., `http://127.0.0.1:3002/sse`).
- **Step 2:** Connect an `EventSource` to that URL. When the server confirms the session, it sends an `endpoint` URL.
- **Step 3:** Send an MCP JSON-RPC `list_tools` request via a `POST fetch()` to that endpoint. Render the results in the sidebar.
- **Step 4 (Chat):** When the user sends a message, format the tools, call the LM Studio API (e.g., `http://localhost:1234/v1/chat/completions`) using pure `fetch()`. Hand-roll the tool execution loop in JS, injecting "calling tool..." status bubbles into the UI.

## 4. Next Steps to Build This

We can build this static MVP entirely in the `tg_fe` directory.

1. **Update Python Server (CORS):** First, we need a 3-line update to `server_rd_json.py` to enable Starlette `CORSMiddleware`, so the browser is allowed to connect to port 3002.
2. **Setup Folder:** Create `tg_fe/mcp.json`, `tg_fe/index.html`, `tg_fe/style.css`, and `tg_fe/app.js`.
3. **Write JS Client:** Code the Vanilla JS logic to read the config, connect to SSE, request tools, and orchestrate with LM Studio.
4. **Style the MVP:** Add the Telegram-like UI and interactions.
5. **Run:** You serve the folder with `python -m http.server` and open it in a browser.
