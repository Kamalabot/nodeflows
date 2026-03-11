"""
Part 2 — Model Layer (/chat endpoint)

LM Studio client setup and the agentic tool-call loop.
"""

from openai import AsyncOpenAI

from starlette.requests import Request
from starlette.responses import JSONResponse

from tools_config import TOOL_DEFS, execute_tool

# ── LM Studio client (OpenAI-compatible API) ─────────────────────────
LM_STUDIO_BASE_URL = "http://localhost:1234/v1"
LM_STUDIO_MODEL = "qwen2.5-7b-instruct"  # change to your loaded model
MAX_TOOL_ROUNDS = 5  # safety limit for tool-call loops

llm = AsyncOpenAI(base_url=LM_STUDIO_BASE_URL, api_key="lm-studio")

# Build OpenAI-compatible tool definitions once from the shared config
OPENAI_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": t["name"],
            "description": t["description"],
            "parameters": {"type": "object", "properties": {}},
        },
    }
    for t in TOOL_DEFS
]


async def chat_endpoint(request: Request) -> JSONResponse:
    """
    POST /chat
    Body: { "prompt": "What is the current CPU usage?" }

    Sends the prompt to LM Studio with the available tools.
    Runs a tool-call loop until the model produces a final text answer.
    Returns: { "response": "...", "tool_calls_made": [...] }
    """
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON body"}, status_code=400)

    prompt = body.get("prompt")
    if not prompt:
        return JSONResponse({"error": "Missing 'prompt' field"}, status_code=400)

    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful assistant with access to real-time PLC and "
                "PC health data via tools. Use the tools to answer the user's "
                "questions with live data. Be concise."
            ),
        },
        {"role": "user", "content": prompt},
    ]

    tool_calls_log = []

    for _round in range(MAX_TOOL_ROUNDS):
        response = await llm.chat.completions.create(
            model=LM_STUDIO_MODEL,
            messages=messages,
            tools=OPENAI_TOOLS,
            tool_choice="auto",
        )

        choice = response.choices[0]

        # If the model has no tool calls, we have the final answer
        if not choice.message.tool_calls:
            return JSONResponse({
                "response": choice.message.content,
                "tool_calls_made": tool_calls_log,
            })

        # Append the assistant message (with tool_calls) to the conversation
        messages.append(choice.message)

        # Execute each tool call and feed results back
        for tc in choice.message.tool_calls:
            tool_name = tc.function.name
            result_text = await execute_tool(tool_name)

            tool_calls_log.append({
                "tool": tool_name,
                "result_preview": result_text[:200],
            })

            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result_text,
            })

    # Exhausted the loop — ask for a final answer without tools
    messages.append({
        "role": "user",
        "content": "Please summarise your findings based on the tool results above.",
    })
    final = await llm.chat.completions.create(
        model=LM_STUDIO_MODEL, messages=messages
    )
    return JSONResponse({
        "response": final.choices[0].message.content,
        "tool_calls_made": tool_calls_log,
    })
