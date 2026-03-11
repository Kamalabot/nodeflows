# tg_py: Chainlit Chat UI

`tg_py` is a production-ready, Telegram-style Chat UI designed to act as the primary interface for your local LLMs (via LM Studio) and Node-RED tools. 

It completely bypasses the browser CORS and SSE limitations inherent in pure HTML/JS MCP clients by moving the orchestrator logic to the Python backend.

## Architecture

```mermaid
graph TD
    User((User)) <--> |Browser UI (Port 8000)| CL[Chainlit Backend<br/>tg_py/app.py]
    CL <--> |OpenAI SDK| LLM[LM Studio API]
    CL <--> |HTTP Requests| Backend[Node-RED API]
```

1. **The UI**: Provided out-of-the-box by the Chainlit framework (React-based, dark-mode ready, sleek).
2. **The Backend**: `app.py` intercepts incoming messages. It manages the conversation history independently of the browser.
3. **The Agentic Loop**: Instead of using an MCP Client SDK, `app.py` loads the tools directly from your JSON definitions, converts them to OpenAI Tool schemas, and passes them to LM Studio. When the LLM requests a tool call, the Chainlit backend executes the HTTP request natively (bypassing browser CORS) and uses `cl.Step` to show the user a loading/reasoning indicator in the UI.

## File Breakdown
- `app.py`: The cohesive orchestrator. Handles `@cl.on_chat_start`, `@cl.on_message`, native slash commands, and the LLM tool-calling loop.
- `pyproject.toml` / `.venv`: Managed by `uv`.

## Features
- **Native Slash Commands**: You can type `/help`, `/plc`, or `/health` in the chat to instantly execute python functions directly without involving the LLM at all. This gives it the snappy feel of a true Telegram bot.
- **Agentic Interactions**: You can naturally ask "Is there an anomaly in the PLC data?" The LLM will use the tools and respond conversationally.
- **Production Ready**: Because it runs on Python under the hood, this approach easily scales to add Oauth logins, database persistence for chat history, and multi-user scaling.

## How to Run

1. Ensure **LM Studio** is running its local server on port `1234`.
2. Ensure **Node-RED** is running on port `1880`.
3. Start the Chainlit app:

```bash
cd tg_py
uv run chainlit run app.py -w
```

4. Open `http://localhost:8000` in your browser.
