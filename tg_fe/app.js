// Initialize Lucide Icons
lucide.createIcons();

// DOM Elements
const serverList = document.getElementById('server-list');
const toolList = document.getElementById('tool-list');
const statusDot = document.getElementById('connection-dot');
const statusText = document.getElementById('connection-status');
const chatMessages = document.getElementById('chat-messages');
const promptInput = document.getElementById('prompt-input');
const sendBtn = document.getElementById('send-btn');

// State
let mcpEndpoint = null;      // Will be set from mcp.json
let mcpSessionUrl = null;    // URL dynamically assigned by SSE
let mcpTools = [];           // Fetched tools
let isGenerating = false;    // LLM state

const LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions";
const LM_STUDIO_MODEL = "qwen2.5-7b-instruct"; // Must match your loaded model

// ── UI Helpers ──────────────────────────────────────────────────────
function updateStatus(state, text) {
    statusDot.className = `status-dot ${state}`;
    statusText.textContent = text;
}

function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function appendMessage(role, content, isSystem = false) {
    const div = document.createElement('div');
    if (isSystem) {
        div.className = 'message system';
    } else {
        div.className = `message ${role === 'user' ? 'user' : 'bot'}`;
    }

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.innerHTML = content; // Allows inserting HTML badges

    div.appendChild(contentDiv);
    chatMessages.appendChild(div);
    scrollToBottom();
    return div;
}

// ── Step 1: Initialization & MCP Connection ─────────────────────────

async function init() {
    updateStatus('checking', 'Reading mcp.json...');
    
    try {
        const res = await fetch('mcp.json');
        const config = await res.json();
        
        // Find the first server URL
        const serverName = Object.keys(config.mcpServers)[0];
        mcpEndpoint = config.mcpServers[serverName].url;
        
        serverList.innerHTML = `
            <li>
                <span>${serverName}</span>
                <i data-lucide="link" width="16" height="16"></i>
            </li>`;
        lucide.createIcons();

        connectMCP(mcpEndpoint);

    } catch (err) {
        console.error(err);
        serverList.innerHTML = `<li class="error">Failed to load mcp.json</li>`;
        updateStatus('offline', 'Config Error');
    }
}

function connectMCP(sseUrl) {
    updateStatus('checking', 'Connecting to SSE...');
    
    // Use polyfill to inject headers
    const eventSource = new EventSourcePolyfill(sseUrl, {
        headers: {
            'Accept': 'text/event-stream'
        }
    });

    eventSource.oninfo = (event) => {
        // Starlette streamable_http sends an initialization event
        // But often we just wait for the endpoint event
        console.log("SSE Info:", event.data);
    };

    eventSource.addEventListener("endpoint", async (event) => {
        // The server tells us where to send POST requests
        mcpSessionUrl = event.data;
        console.log("MCP Session established. POST endpoint:", mcpSessionUrl);
        updateStatus('online', 'Connected');
        
        // Now fetch tools
        await fetchTools();
    });

    eventSource.onerror = (err) => {
        console.error("SSE Error:", err);
        updateStatus('offline', 'Disconnected');
    };
}

// ── Step 2: Fetch Tools from MCP ────────────────────────────────────

async function fetchTools() {
    if (!mcpSessionUrl) return;

    try {
        // MCP JSON-RPC payload for tools/list
        const payload = {
            jsonrpc: "2.0",
            id: 1,
            method: "tools/list",
            params: {}
        };

        const res = await fetch(mcpSessionUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await res.json();
        if (data.result && data.result.tools) {
            mcpTools = data.result.tools;
            renderToolsSidebar();
        }
    } catch (err) {
        console.error("Failed to fetch tools:", err);
        toolList.innerHTML = `<li class="error">Failed to load tools</li>`;
    }
}

function renderToolsSidebar() {
    toolList.innerHTML = '';
    
    if (mcpTools.length === 0) {
        toolList.innerHTML = `<li class="empty-state">No tools found</li>`;
        return;
    }

    mcpTools.forEach(tool => {
        const li = document.createElement('li');
        li.className = 'tool-item';
        li.innerHTML = `
            <div>
                <strong><i data-lucide="wrench" width="14" height="14"></i> ${tool.name}</strong>
                <span class="desc">${tool.description}</span>
            </div>
        `;
        toolList.appendChild(li);
    });
    lucide.createIcons();
}

// ── Step 3: Tool Execution (MCP call_tool) ──────────────────────────

async function executeMcpTool(toolName, args, messageNode) {
    if (!mcpSessionUrl) throw new Error("No active MCP session");

    // Update UI bubble to show running
    messageNode.querySelector('.message-content').innerHTML += `
        <div class="tool-badge">
            <i data-lucide="loader-2" class="spinner" width="12" height="12"></i> 
            Calling ${toolName}...
        </div>
    `;
    lucide.createIcons();
    scrollToBottom();

    // MCP JSON-RPC payload for tools/call
    const payload = {
        jsonrpc: "2.0",
        id: Date.now(),
        method: "tools/call",
        params: {
            name: toolName,
            arguments: args || {}
        }
    };

    const res = await fetch(mcpSessionUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    });

    const data = await res.json();
    
    // Update badge to checkmark
    const content = messageNode.querySelector('.message-content');
    content.innerHTML = content.innerHTML.replace('loader-2', 'check').replace('spinner', '');
    lucide.createIcons();
    
    if (data.result && data.result.content && data.result.content.length > 0) {
        return data.result.content[0].text;
    }
    return JSON.stringify(data.result);
}


// ── Step 4: LLM Chat Loop ───────────────────────────────────────────

let chatHistory = [
    {
        role: "system",
        content: "You are a helpful assistant with access to real-time PLC and PC health data via tools. Use the tools to answer the user's questions with live data. Be concise."
    }
];

async function handleSend() {
    const prompt = promptInput.value.trim();
    if (!prompt || isGenerating) return;

    // Reset UI
    promptInput.value = '';
    promptInput.style.height = 'auto'; // reset textarea height
    isGenerating = true;
    sendBtn.disabled = true;

    // Show user message
    appendMessage('user', prompt);
    chatHistory.push({ role: "user", content: prompt });

    // Show bot thinking bubble
    const botBubble = appendMessage('bot', '<i data-lucide="loader-2" class="spinner" width="16" height="16"></i> Thinking...');
    lucide.createIcons();

    // Prepare OpenAI tools format from MCP tools
    const openAiTools = mcpTools.map(t => ({
        type: "function",
        function: {
            name: t.name,
            description: t.description,
            parameters: { type: "object", properties: {} } // Simple default
        }
    }));

    // Start LLM Loop (max 5 rounds)
    for (let round = 0; round < 5; round++) {
        try {
            const body = {
                model: LM_STUDIO_MODEL,
                messages: chatHistory,
            };
            if (openAiTools.length > 0) {
                body.tools = openAiTools;
                body.tool_choice = "auto";
            }

            const res = await fetch(LM_STUDIO_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
            });

            const data = await res.json();
            const choice = data.choices[0];

            // If no tool calls, we have the final answer!
            if (!choice.message.tool_calls) {
                // Update final message bubble
                botBubble.querySelector('.message-content').innerHTML = choice.message.content.replace(/\n/g, '<br>');
                chatHistory.push(choice.message);
                break;
            }

            // Append assistant message with tool calls to history
            chatHistory.push(choice.message);

            // Execute each tool call
            for (const tc of choice.message.tool_calls) {
                const toolName = tc.function.name;
                const toolArgs = JSON.parse(tc.function.arguments || "{}");
                
                // Execute against MCP server
                const resultText = await executeMcpTool(toolName, toolArgs, botBubble);

                // Add result to history so LLM can read it
                chatHistory.push({
                    role: "tool",
                    tool_call_id: tc.id,
                    content: resultText
                });
            }

            // Loop continues: will send the tool results back to LLM for final answer

        } catch (err) {
            console.error(err);
            botBubble.querySelector('.message-content').innerHTML = `Error communicating with LM Studio.<br><small>${err.message}</small>`;
            break;
        }
    }

    isGenerating = false;
    sendBtn.disabled = false;
    promptInput.focus();
}

// ── Event Listeners ─────────────────────────────────────────────────

sendBtn.addEventListener('click', handleSend);

promptInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSend();
    }
});

// Auto-resize textarea
promptInput.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = (this.scrollHeight) + 'px';
});

// Start the app
init();
