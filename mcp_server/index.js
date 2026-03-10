import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { CallToolRequestSchema, ListToolsRequestSchema } from "@modelcontextprotocol/sdk/types.js";
import axios from "axios";

const server = new Server({ name: "nodered-bridge", version: "1.0.0" }, { capabilities: { tools: {} } });

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "get_pc_health",
      description: "Returns CPU and memory layout of the host Windows machine from Node-RED.",
      inputSchema: { type: "object", properties: {} }
    },
    {
      name: "get_plc_data",
      description: "Returns simulated live Modbus PLC data (sensors, counters, patterns) from Node-RED.",
      inputSchema: { type: "object", properties: {} }
    }
  ]
}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  if (request.params.name === "get_pc_health") {
    const response = await axios.get("http://localhost:1880/api/pc_health");
    return { content: [{ type: "text", text: String(response.data) }] };
  }
  
  if (request.params.name === "get_plc_data") {
    const response = await axios.get("http://127.0.0.1:1880/api/scada");
    return { content: [{ type: "text", text: JSON.stringify(response.data, null, 2) }] };
  }
  
  throw new Error("Tool not found");
});

const transport = new StdioServerTransport();
await server.connect(transport);
