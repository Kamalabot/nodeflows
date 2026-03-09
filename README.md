# Node-RED Mastery: 10 Exercises to Level Up

Here are 10 progressively challenging and detailed exercises to help you master Node-RED. These exercises move from basic data manipulation to system integration, and finally to modern AI tool integration via the Model Context Protocol (MCP).

---

## Part 1: Core Concepts & Data Manipulation

### Exercise 1: The Timestamp Transformer
**Goal:** Learn how to trigger flows periodically, write basic JavaScript, and debug outputs.
**Steps:**
1. Drag an **Inject** node (from the *Common* palette) onto the workspace.
2. Double-click the Inject node to open its settings. 
3. Leave the payload as `timestamp` (the default). In Node-RED v4.1, look for the **Repeat** section near the bottom of the dialog. Change the dropdown from "none" to **"interval"**, and set it to **every 5 seconds**. Click Done.
4. Drag a **Function** node (from the *Function* palette) next to it.
4. Double-click the Function node and add this JavaScript code:
   ```javascript
   // The initial payload is a timestamp in milliseconds
   let date = new Date(msg.payload);
   
   // We are converting the timestamp to a human-readable ISO string
   msg.payload = `Current Time: ${date.toISOString()}`;
   return msg;
   ```
5. Drag a **Debug** node and connect them logically: `Inject -> Function -> Debug`.
6. Click **Deploy**. Open the debug sidebar (bug icon) to watch the messages stream in every 5 seconds.

### Exercise 2: The Weather Router
**Goal:** Learn to work with JSON objects and conditionally route messages based on data values.
**Steps:**
1. Create an **Inject** node. Change the payload type to JSON and paste: `{"city": "Paris", "temp": 22}`. Give it a name like "Test Temp = 22".
2. Create a second **Inject** node with JSON payload: `{"city": "Madrid", "temp": 30}`. Named "Test Temp = 30".
3. Drag a **Switch** node. Double-click it. Ensure the Property is `msg.payload.temp`.
4. Add two rules to the Switch node:
   * `> 25` (This creates output port 1)
   * `<= 25` (This creates output port 2)
5. Drag two **Change** nodes.
   * Attach the first Change node to Port 1 of the Switch. Configure it: `Set msg.payload to "Hot!"`.
   * Attach the second Change node to Port 2 of the Switch. Configure it: `Set msg.payload to "Cool!"`.
6. Attach a **Debug** node to the output of both Change nodes and **Deploy**. Clicking either Inject node should print the correct classification.

### Exercise 3: API Fetch & Extract
**Goal:** Learn to make HTTP requests and extract specific nested JSON data without using JavaScript.
**Steps:**
1. Create a manual **Inject** node (default timestamp).
2. Drag an **HTTP Request** node (from the *Network* palette). Double click it and set the URL to `https://catfact.ninja/fact`. Set the Method to `GET` and Return to `a parsed JSON object`.
3. Drag a **Change** node after it. 
   * The API returns something like `{"fact": "Cats sleep 70% of their lives.", "length": 30}`. 
   * Configure the Change node with the rule: `Set msg.payload to msg.payload.fact`. This extracts just the fact string and discards the rest of the object.
4. Add a **Debug** node, connect the flow: `Inject -> HTTP Request -> Change -> Debug`. **Deploy** and generate cat facts!

### Exercise 4: The File Logger
**Goal:** Learn how to create HTTP webhooks (endpoints) and write data directly to your local file system.
**Steps:**
1. Drag an **HTTP In** node (from the *Network* palette). Set Method to `GET` and URL to `/log`.
2. Drag a **Functions** node after it with this code:
   ```javascript
   // Extract the IP of the requester (from req.ip) and the current timestamp
   msg.payload = `[${new Date().toISOString()}] Visited by IP: ${msg.req.ip}\n`;
   return msg;
   ```
3. Drag a **File** out node (from the *Storage* palette). Set the filename to `d:\gitFolders\nodeflows\visits.log`. Ensure the Action is set to `append to file`.
4. Drag an **HTTP Response** node and attach it right after the Function node. Configure it to send `{"status": "Logged!"}` as a JSON response. (Crucial, or the browser will hang waiting for a response!).
5. **Deploy**. Visit `http://localhost:1880/log` in a web browser. Then check your `nodeflows` directory for the newly created log file!

---

## Part 2: Hardware & System Integration

### Exercise 5: OS Information Extraction (Basic)
**Goal:** Learn how to install and utilize third-party community nodes for system-level data.
**Steps:**
1. Go to the top-right menu (hamburger icon) > **Manage palette**. Click the **Install** tab, search for `node-red-contrib-os`, and click install. Wait for the notification.
2. In your palette, you will now have a new OS node (usually named `OS` or `sysinfo`). Drag it to the workspace.
3. Configure the OS node to output something like "Memory Usage" or "CPU Load" (depending on the exact package installed).
4. Connect a repeating **Inject** node (e.g., every 10 seconds) to its input.
5. Add a **Debug** node to its output. **Deploy** and inspect the rich system data JSON arriving in your debug tab!

### Exercise 6: Executing System Commands
**Goal:** Learn how to run underlying OS terminal commands and utilize Regex to extract text.
**Steps:**
1. Drag an **Inject** node.
2. Drag an **Exec** node (from the *Advanced* palette). Double click it. Set the command to `systeminfo` or `ipconfig`. Leave the Append box empty.
3. The Exec node has 3 outputs: standard output (stdout), error output (stderr), and return code. 
4. Drag a **Function** node and connect it to output 1 (stdout). The data arrives as a giant raw string. Let's parse out an IP address using Regex!
   ```javascript
   // Look for an IPv4 address pattern (e.g., "IPv4 Address. . . . . . . . . . . : 192.168.1.100")
   const str = msg.payload.toString();
   const regex = /IPv4 Address[^:]+:\s*([0-9.]+)/i; 
   const match = str.match(regex);
   
   if (match && match.length > 1) {
       msg.payload = "Your local IP is: " + match[1];
   } else {
       msg.payload = "Could not find IP.";
   }
   return msg;
   ```
5. Output to a **Debug** node and **Deploy**. Ensure it successfully parsed out your IP Address.

### Exercise 7: Periodic Health Dashboard
**Goal:** Learn how to install and build graphical user interfaces for your node workflows using modern web frameworks.
**Steps:**
1. The old `node-red-dashboard` is deprecated. Install the modern replacement, `@flowfuse/node-red-dashboard`, via the **Manage palette** menu.
2. Create an **Inject** node and configure its "Repeat" dropdown to an "interval" of every 5 seconds. Connect it to trigger an **Exec** node running `wmic cpu get loadpercentage` (A fast way to get CPU load on Windows).
3. Connect a **Function** node to the stdout of the Exec node to clean up the number:
   ```javascript
   // Remove non-numeric characters (like "LoadPercentage")
   const loadStr = msg.payload.toString().replace(/[^0-9]/g, '');
   msg.payload = parseInt(loadStr, 10);
   return msg;
   ```
4. Drag a **ui_gauge** node (from the newly installed *Dashboard 2.0* palette). Double-click it. 
   - Click the pencil icon next to "Group" to add a new **UI Group** named "PC Health".
   - Inside the Group config, click the pencil next to "Page" to add a new **UI Page** named "Home".
   - Inside the Page config, click the pencil next to "Base" to add a new **UI Base**.
   - Click Add/Update on Base, then Page, then Group to return to the Gauge settings.
   - Set the `min` to 0 and `max` to 100. Click Done.
5. Connect your cleanup Function directly to the Gauge. **Deploy**.
6. Visit `http://localhost:1880/dashboard` in your browser. You should now see a modern, live, updating gauge of your CPU usage!

---

## Part 3: Advanced APIs & Context

### Exercise 8: State Tracking with Context
**Goal:** Learn how to persist data across different flow runs utilizing Node-RED Context.
**Steps:**
1. Drag an **HTTP In** node listening to GET `/toggle`.
2. Drag a **Function** node:
   ```javascript
   // Retrieve the current state from flow context (default to false if it doesn't exist yet)
   let currentState = flow.get("mySwitchState") || false;
   
   // Toggle it
   let newState = !currentState;
   
   // Save it back to context so the next run remembers it
   flow.set("mySwitchState", newState);
   
   msg.payload = `The switch is now: ${newState ? 'ON' : 'OFF'}`;
   return msg;
   ```
3. Drag an **HTTP Response** node so the browser receives the text.
4. **Deploy** and hit `http://localhost:1880/toggle` manually in the browser multiple times. Observe the text alternating states. This state will survive until Node-RED is restarted!

### Exercise 9: The Catch & Error Handler
**Goal:** Learn to gracefully intercept programmatic errors instead of crashing nodes silently.
**Steps:**
1. Drag an **Inject** node.
2. Drag an **HTTP Request** node and put an intentional garbage URL in it: `http://this-url-is-invalid-and-fake.com`.
3. Try running it to a Debug node. You should see an ugly red error toast popup "Error: getaddrinfo ENOTFOUND..."
4. Now, drag a **Catch** node (from the *Common* palette). In its settings, check "Catch errors from all nodes".
5. Connect the Catch node output to a **Function** node:
   ```javascript
   msg.payload = `GLOBAL ERROR CAUGHT!
   Node ID: ${msg.error.source.id}
   Error Message: ${msg.error.message}`;
   return msg;
   ```
6. Connect this function to a **File** output node, appending to `errors.log`, and also output to a **Debug** node.
7. **Deploy**. When the HTTP node fails, the failure flow is elegantly intercepted, parsed into a friendly message, and logged safely.

---

## Part 4: Introduction to MCP Nodes (Model Context Protocol)

### Exercise 10: Building an AI Tool Interface (HTTP Bridge to MCP)
**Goal:** Expose your Node-RED flows to an AI using a standalone Node.js MCP Server that bridges requests via standard HTTP, avoiding the complexities of internal Node-RED SSE servers.

**Context:** Instead of running the MCP server *inside* Node-RED, we will create a lightweight Node.js script that acts as a standard stdio MCP Server. When the AI client (like Cursor or Claude) calls a tool, this Node.js script makes a simple HTTP request to your Node-RED flow, which does the actual work and returns the result.

**Steps:**
1. In Node-RED, drag an **HTTP In** node onto the workspace. Configure it with Method: `GET` and URL: `/api/pc_health`.
2. Connect it to an **Exec** node (running `systeminfo`).
3. Connect the Exec node's stdout to a **Function** node to trim and clean the output:

   ```javascript
   msg.payload = "Extracted Host Spec Data: \n" + msg.payload.toString().substring(0, 500);
   return msg;
   ```

4. Connect the Function node to an **HTTP Response** node. **Deploy** your flow. You can test it by visiting `http://localhost:1880/api/pc_health` in your browser.
5. Create a new folder on your computer for your bridge server, open a terminal there, and run:
   ```bash
   npm init -y
   npm install @modelcontextprotocol/sdk axios
   ```
6. Inside that folder, create an `index.js` file with this standalone MCP server code:
   ```javascript
   import { Server } from "@modelcontextprotocol/sdk/server/index.js";
   import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
   import { CallToolRequestSchema, ListToolsRequestSchema } from "@modelcontextprotocol/sdk/types.js";
   import axios from "axios";

   const server = new Server({ name: "nodered-bridge", version: "1.0.0" }, { capabilities: { tools: {} } });

   server.setRequestHandler(ListToolsRequestSchema, async () => ({
     tools: [{
       name: "get_pc_health",
       description: "Returns CPU and memory layout of the host Windows machine from Node-RED.",
       inputSchema: { type: "object", properties: {} }
     }]
   }));

   server.setRequestHandler(CallToolRequestSchema, async (request) => {
     if (request.params.name === "get_pc_health") {
       const response = await axios.get("http://localhost:1880/api/pc_health");
       return { content: [{ type: "text", text: String(response.data) }] };
     }
     throw new Error("Tool not found");
   });

   const transport = new StdioServerTransport();
   await server.connect(transport);
   ```
   *Note: Ensure `"type": "module"` is added to your `package.json` so `import` statements work!*
7. To connect your AI client, update its `mcp_config.json` to spawn your new bridge script via `stdio`:
   ```json
   {
     "mcpServers": {
       "nodered-bridge": {
         "command": "node",
         "args": ["/absolute/path/to/your/bridge/folder/index.js"]
       }
     }
   }
   ```
   Once configured, the AI will use this standard Node.js server to talk to your Node-RED flows seamlessly!
