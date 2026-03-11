import json
import traceback
import chainlit as cl
from contextlib import AsyncExitStack
from openai import AsyncOpenAI
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

# ── Configuration ────────────────────────────────────────────────────────
LM_STUDIO_BASE_URL = "http://localhost:1234/v1"
LM_STUDIO_MODEL = "qwen2.5-7b-instruct"
MCP_SERVER_URL = "http://127.0.0.1:3001/sse"

# Initialize OpenAI Async Client pointing to LM Studio
client = AsyncOpenAI(base_url=LM_STUDIO_BASE_URL, api_key="lm-studio")

# ── Chainlit Chat Logic ──────────────────────────────────────────────────

@cl.on_chat_start
async def on_chat_start():
    # Setup MCP client for this user session
    try:
        exit_stack = AsyncExitStack()
        cl.user_session.set("mcp_exit_stack", exit_stack)
        
        # Connect using Streamable HTTP Client
        transport = await exit_stack.enter_async_context(streamable_http_client(MCP_SERVER_URL))
        read_stream, write_stream, get_session_id = transport
        
        session = await exit_stack.enter_async_context(ClientSession(read_stream, write_stream))
        await session.initialize()
        
        cl.user_session.set("mcp_session", session)
        
        # Dynamically load tools
        tools_response = await session.list_tools()
        mcp_tools = tools_response.tools
        
        # Convert to OpenAI Tool Format
        openai_tools = []
        tool_names = []
        for t in mcp_tools:
            tool_names.append(t.name)
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description or "No description provided.",
                    "parameters": t.inputSchema or {
                        "type": "object",
                        "properties": {},
                    },
                }
            })
            
        cl.user_session.set("openai_tools", openai_tools)
        
        # Initialize conversation history
        cl.user_session.set(
            "message_history",
            [
                {
                    "role": "system",
                    "content": "You are a helpful industrial agent. Use the provided tools to fetch live PLC and PC health data to answer user queries. Be concise and friendly."
                }
            ],
        )
        
        # Notify UI of successful connection and tools
        tools_list = "\n".join([f"- `{name}`" for name in tool_names])
        welcome_msg = f"🟢 **Connected to MCP Server!**\n\n**Available Tools:**\n{tools_list}\n\nType `/help` for commands or ask me a question!"
        await cl.Message(content=welcome_msg).send()
        
    except Exception as e:
        traceback.print_exc()
        await cl.Message(content=f"🔴 **Failed to connect to MCP Server:** {str(e)}\n\nPlease ensure your MCP Server is running at `{MCP_SERVER_URL}`.").send()


@cl.on_chat_end
async def on_chat_end():
    # Clean up the MCP connections
    exit_stack = cl.user_session.get("mcp_exit_stack")
    if exit_stack:
        await exit_stack.aclose()


@cl.on_message
async def on_message(message: cl.Message):
    mcp_session = cl.user_session.get("mcp_session")
    openai_tools = cl.user_session.get("openai_tools")
    
    if not mcp_session or not openai_tools:
        await cl.Message(content="MCP Server is not connected. Please restart the chat (`New Chat` button on the left) once the server is running.").send()
        return

    # ── 1. Slash Commands ──
    if message.content.startswith("/"):
        cmd = message.content.split()[0].lower()
        if cmd == "/help":
            await cl.Message(content="**Available Commands:**\n- `/help` : Show this message\n- `/plc` : Instantly fetch PLC data\n- `/health` : Instantly fetch PC health").send()
        elif cmd == "/plc":
            async with cl.Step(name="Fetching PLC Data...") as step:
                try:
                    result = await mcp_session.call_tool("get_plc_data", {})
                    output = result.content[0].text if result.content else "No text returned"
                    step.output = output
                    await cl.Message(content=f"```json\n{output}\n```").send()
                except Exception as e:
                    await cl.Message(content=f"Error: {e}").send()
        elif cmd == "/health":
            async with cl.Step(name="Fetching PC Health...") as step:
                try:
                    result = await mcp_session.call_tool("get_pc_health", {})
                    output = result.content[0].text if result.content else "No text returned"
                    step.output = output
                    await cl.Message(content=f"```json\n{output}\n```").send()
                except Exception as e:
                    await cl.Message(content=f"Error: {e}").send()
        else:
            await cl.Message(content=f"Unknown command: `{cmd}`. Type `/help`.").send()
        return

    # ── 2. Agentic LLM Loop ──
    message_history = cl.user_session.get("message_history")
    message_history.append({"role": "user", "content": message.content})

    msg = cl.Message(content="")
    await msg.send()

    MAX_ROUNDS = 5
    for round_num in range(MAX_ROUNDS):
        try:
            response = await client.chat.completions.create(
                model=LM_STUDIO_MODEL,
                messages=message_history,
                tools=openai_tools,
                tool_choice="auto",
                stream=False
            )
        except Exception as e:
            await cl.Message(content=f"Error connecting to LM Studio: {str(e)}").send()
            break

        choice = response.choices[0]

        if not choice.message.tool_calls:
            final_text = choice.message.content or ""
            msg.content = final_text
            await msg.update()
            
            message_history.append({"role": "assistant", "content": final_text})
            break

        message_history.append(choice.message)

        for tool_call in choice.message.tool_calls:
            tool_name = tool_call.function.name
            
            async with cl.Step(name=f"Executing Tool: {tool_name}") as step:
                # Parse arguments safely
                try:
                    args = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    args = {}
                step.input = args
                
                # Execute the tool dynamically via the true MCP Session
                try:
                    result = await mcp_session.call_tool(tool_name, args)
                    result_text = result.content[0].text if result.content else "Executed tool but no text was returned."
                except Exception as e:
                    result_text = f"Error executing tool: {str(e)}"
                    
                step.output = result_text

            message_history.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": tool_name,
                "content": str(result_text)
            })

