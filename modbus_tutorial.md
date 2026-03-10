# Node-RED Modbus Tutorial: Complete Guide to `node-red-contrib-modbus`

A comprehensive, step-by-step tutorial covering the Modbus protocol and every node in the `node-red-contrib-modbus` package for Node-RED.

---

## 1. What is Modbus?

**Modbus** is one of the oldest and most widely used serial communication protocols in industrial automation (created by Modicon in 1979). It enables a **client** (master) to read and write data stored on a **server** (slave) using simple numerical addresses.

### Why Use Modbus with Node-RED?

- **Universally supported** by PLCs, sensors, actuators, VFDs, and other industrial hardware
- **Simple protocol** — easy to debug and integrate
- **Node-RED's low-code approach** makes it fast to build Modbus dashboards, loggers, and controllers

### Modbus Communication Types

| Type | Transport | Typical Use |
|------|-----------|-------------|
| **Modbus TCP** | Ethernet (IP + Port 502) | Modern PLCs, gateways |
| **Modbus RTU** | Serial (RS-485/RS-232) | Legacy devices, field instruments |
| **Modbus ASCII** | Serial (RS-485/RS-232) | Older devices, human-readable frames |
| **Modbus UDP** | Ethernet (IP + Port) | Lightweight, connectionless |

### The Four Modbus Data Types

Modbus organizes data into four address spaces:

| Data Type | Address Prefix | Size | Access | Typical Use |
|-----------|----------------|------|--------|-------------|
| **Coils** | 0x (00001–09999) | 1-bit | Read/Write | Relays, digital outputs |
| **Discrete Inputs** | 1x (10001–19999) | 1-bit | Read Only | Switches, digital inputs |
| **Input Registers** | 3x (30001–39999) | 16-bit | Read Only | Analog sensor readings |
| **Holding Registers** | 4x (40001–49999) | 16-bit | Read/Write | Configuration, setpoints |

> [!IMPORTANT]
> **Zero-Based Addressing:** Node-RED Modbus nodes use **zero-based** addresses. If your PLC documentation says "Holding Register 40001", you enter address `0` in the node. Register 40010 = address `9`.

### Modbus Function Codes (FC)

Function codes tell the server what operation to perform:

| FC | Name | Data Type | Operation |
|----|------|-----------|-----------|
| **FC1** | Read Coil Status | Coils | Read multiple coil bits |
| **FC2** | Read Discrete Inputs | Discrete Inputs | Read multiple input bits |
| **FC3** | Read Holding Registers | Holding Registers | Read multiple 16-bit registers |
| **FC4** | Read Input Registers | Input Registers | Read multiple 16-bit registers |
| **FC5** | Write Single Coil | Coils | Write one coil ON/OFF |
| **FC6** | Write Single Register | Holding Registers | Write one 16-bit value |
| **FC15** | Write Multiple Coils | Coils | Write multiple coil bits |
| **FC16** | Write Multiple Registers | Holding Registers | Write multiple 16-bit values |

---

## 2. Installing `node-red-contrib-modbus`

### Method 1: Palette Manager (Recommended)

1. Open your Node-RED editor at `http://localhost:1880`
2. Click the **hamburger menu** (☰) → **Manage palette**
3. Go to the **Install** tab
4. Search for `node-red-contrib-modbus`
5. Click **Install** and confirm the popup

### Method 2: Command Line

Stop Node-RED first, then run from your Node-RED user directory:

```bash
cd d:\gitFolders\nodeflows
npm install node-red-contrib-modbus
```

Restart Node-RED after installation.

### Verify Installation

After installation, you should see these new nodes in your palette under the **Modbus** category:

- `modbus-client` (configuration node)
- `modbus-read`
- `modbus-getter`
- `modbus-flex-getter`
- `modbus-write`
- `modbus-flex-write`
- `modbus-server`
- `modbus-flex-server`
- `modbus-response`
- `modbus-response-filter`
- `modbus-flex-connector`
- `modbus-flex-sequencer`
- `modbus-flex-fc`
- `modbus-queue-info`
- `modbus-io-config`

---

## 3. Complete Node Reference

### 3.1 `modbus-client` (Configuration Node)

**Purpose:** Defines the connection to a Modbus server/device. This is a **config node** — you don't drag it onto the canvas; instead, it's created when you configure a server connection inside any Modbus node.

**Key Settings:**

| Field | Description | Example |
|-------|-------------|---------|
| **Type** | TCP, UDP, Serial RTU, Serial ASCII | `TCP` |
| **Host** | IP address of the Modbus device | `192.168.1.100` |
| **Port** | TCP/UDP port number | `502` (default) |
| **Unit ID** | Slave/device address (0–255) | `1` |
| **TCP Type** | Default, Telnet, TCP-RTU | `Default` |
| **Reconnect Timeout** | Auto-reconnect delay (ms) | `2000` |

**For Serial connections (RTU/ASCII):**

| Field | Description | Example |
|-------|-------------|---------|
| **Serial Port** | COM port path | `COM3` or `/dev/ttyUSB0` |
| **Baud Rate** | Communication speed | `9600` |
| **Data Bits** | Bits per frame | `8` |
| **Stop Bits** | Stop bits | `1` |
| **Parity** | Error checking | `None` |

---

### 3.2 `modbus-read`

**Purpose:** Periodically reads a fixed set of Modbus registers or coils on a timer.

**When to use:** When you need to **poll** the same address at regular intervals (e.g., reading a temperature sensor every 5 seconds).

**Configuration:**

| Field | Value |
|-------|-------|
| **FC** | FC1, FC2, FC3, or FC4 |
| **Address** | Starting address (zero-based) |
| **Quantity** | Number of registers/coils to read |
| **Poll Rate** | Interval in seconds |
| **Server** | Select your `modbus-client` config |

**Outputs:**
- **Output 1:** `msg.payload` — array of values read
- **Output 2:** `msg.payload` — Modbus response object (for advanced use)

**Example Flow — Read 4 Holding Registers every 2 seconds:**

```
[Modbus Read] ──► [Debug]
     FC3
     Addr: 0
     Qty: 4
     Rate: 2s
```

```json
// Output msg.payload example:
[100, 250, 0, 1023]
```

---

### 3.3 `modbus-getter`

**Purpose:** Reads Modbus data once when triggered by an incoming message.

**When to use:** When you want to read **on demand** (not on a timer), e.g., triggered by an Inject node or an HTTP request.

**Configuration:** Same as `modbus-read` but without the poll rate. It reads once per incoming `msg`.

> [!CAUTION]
> **`keepMsgProperties` is OFF by default.** This means the node creates a **brand new `msg`** and drops all original properties — including `msg.req` and `msg.res` from an `http in` node. If you're using `modbus-getter` inside an HTTP flow, you **must** enable **"Keep Msg Properties"** in the node settings, or the `http response` node will never receive a response object and the browser will hang forever.

**Example Flow — Read on Button Click:**

```
[Inject] ──► [Modbus Getter] ──► [Debug]
                  FC3
                  Addr: 0
                  Qty: 10
```

---

### 3.4 `modbus-flex-getter`

**Purpose:** A **dynamic** reader — the FC, address, quantity, and unit ID come from the incoming `msg.payload`, not from the node configuration.

**When to use:** When you need to read **different addresses dynamically** based on logic. This is the most flexible read node.

**Input `msg.payload` format:**

```javascript
msg.payload = {
    value: msg.payload,       // pass-through data (optional)
    unitid: 1,                // Modbus slave ID
    fc: 3,                    // Function Code (1, 2, 3, or 4)
    address: 0,               // Starting address (zero-based)
    quantity: 10              // Number of registers/coils
};
return msg;
```

**Example Flow — Dynamic Multi-Address Reader:**

```
[Inject] ──► [Function: Set Params] ──► [Modbus Flex Getter] ──► [Debug]
```

**Function node code:**

```javascript
// Read 5 holding registers starting at address 100
msg.payload = {
    unitid: 1,
    fc: 3,
    address: 100,
    quantity: 5
};
return msg;
```

---

### 3.5 `modbus-write`

**Purpose:** Writes a fixed value to a specific Modbus register or coil when triggered.

**When to use:** When you always write to the **same address** (e.g., a setpoint register).

**Configuration:**

| Field | Description |
|-------|-------------|
| **FC** | FC5 (single coil), FC6 (single register), FC15 (multiple coils), FC16 (multiple registers) |
| **Address** | Target address (zero-based) |
| **Quantity** | Number of items (for FC15/FC16) |
| **Server** | Your `modbus-client` config |

**Input:** `msg.payload` must contain the value(s) to write.

**Example — Write a single holding register:**

```
[Inject: 1500] ──► [Modbus Write] ──► [Debug]
                       FC6
                       Addr: 10
```

**Example — Write multiple registers:**

```javascript
// In a Function node before Modbus Write (FC16)
msg.payload = [100, 200, 300, 400];  // Write 4 registers
return msg;
```

---

### 3.6 `modbus-flex-write`

**Purpose:** A **dynamic** writer — the FC, address, quantity, and unit ID come from `msg.payload`.

**When to use:** When you need to write to **different addresses dynamically**.

**Input `msg.payload` format:**

```javascript
msg.payload = {
    value: [1500],             // Value(s) to write
    unitid: 1,                 // Modbus slave ID
    fc: 6,                     // Function Code (5, 6, 15, or 16)
    address: 10,               // Target address (zero-based)
    quantity: 1                // Number of items
};
return msg;
```

**Example Flow — Dynamic Register Writer:**

```
[Inject] ──► [Function: Build Write] ──► [Modbus Flex Write] ──► [Debug]
```

**Function node code:**

```javascript
// Write value 2500 to holding register 50 on unit 1
msg.payload = {
    value: [2500],
    unitid: 1,
    fc: 6,
    address: 50,
    quantity: 1
};
return msg;
```

---

### 3.7 `modbus-server`

**Purpose:** Creates a **virtual Modbus TCP server** inside Node-RED. Other devices or software can connect to Node-RED as if it were a real PLC.

**When to use:**
- **Testing** — simulate a Modbus device without real hardware
- **Data bridging** — let external Modbus clients read data gathered by Node-RED
- **Training** — learn Modbus without physical devices

**Configuration:**

| Field | Description | Default |
|-------|-------------|---------|
| **Port** | TCP listening port | `10502` |
| **Unit IDs** | List of unit IDs to respond to | `1` |
| **Coils Size** | Number of coils to simulate | `10000` |
| **Registers Size** | Number of registers | `10000` |

**Outputs:**
- **Output 1:** Emits messages when a client reads/writes data
- **Output 2:** Emits error messages

**Example Flow — Simulate a Modbus Device:**

```
                            ┌──► [Debug: Client Activity]
[Modbus Server (port 10502)]┤
                            └──► [Debug: Errors]
```

Then use a **Modbus Read** node pointing to `localhost:10502` to test reading from your simulated server.

---

### 3.8 `modbus-flex-server`

**Purpose:** A **dynamic Modbus TCP server** where you can programmatically set register/coil values by sending messages into the node.

**When to use:** When you want to **push live data** into a virtual Modbus server (e.g., feeding real sensor data from an API into a Modbus-accessible register bank).

**Input `msg.payload` format:**

```javascript
// Set holding register 0 to value 1234
msg.payload = {
    register: "holding",       // "holding", "input", "coils", "discrete"
    address: 0,
    value: [1234, 5678]        // Array of values
};
return msg;
```

---

### 3.9 `modbus-response`

**Purpose:** Formats Modbus read/getter output into a more usable structure. Place it after a read node to transform the raw buffer data.

**When to use:** When you need to **decode** raw Modbus data (e.g., convert two 16-bit registers into a 32-bit float).

**Example Flow:**

```
[Modbus Read] ──► [Modbus Response] ──► [Function: Parse] ──► [Debug]
```

---

### 3.10 `modbus-response-filter`

**Purpose:** Filters Modbus responses based on criteria like the unit ID or I/O address, so you can selectively process only the data you need.

**When to use:** When multiple reads are happening and you only want to react to **specific addresses or devices**.

---

### 3.11 `modbus-flex-connector`

**Purpose:** Dynamically changes the **connection parameters** (IP, port, unit ID) of a `modbus-client` config node at runtime.

**When to use:** When you need to **switch between multiple Modbus devices** using a single set of nodes (e.g., scanning a range of IPs).

**Input:**

```javascript
msg.payload = {
    connectorType: "TCP",
    tcpHost: "192.168.1.200",
    tcpPort: "502",
    unitId: 2
};
return msg;
```

---

### 3.12 `modbus-flex-sequencer`

**Purpose:** Reads from **multiple different addresses in sequence**, one after another, using a single node. Avoids flooding the Modbus bus.

**When to use:** When you need to read many different registers but want **ordered, sequential reads** (not simultaneous).

---

### 3.13 `modbus-flex-fc`

**Purpose:** Sends **any Modbus function code** dynamically. This is the most low-level, flexible node — useful for custom or Device-specific function codes beyond the standard FC1–FC16.

**When to use:** Advanced scenarios where standard read/write nodes don't cover your needs.

---

### 3.14 `modbus-queue-info`

**Purpose:** Monitors the internal Modbus **request queue**. Provides status on how many requests are queued, helping you detect bottlenecks.

**When to use:** When polling many devices and you want to:
- Monitor queue depth ("low", "high", "high-high")
- Trigger alerts when the queue is overloaded
- Send reset commands to clear a stuck queue

**Configuration:**

| Field | Description |
|-------|-------------|
| **Low Level** | Normal queue threshold |
| **High Level** | Warning threshold |
| **High-High Level** | Critical threshold — trigger error alerts |

**Example Flow:**

```
[Inject: every 10s] ──► [Modbus Queue Info] ──► [Switch: high-high?] ──► [Debug: ALERT]
```

---

### 3.15 `modbus-io-config`

**Purpose:** A **configuration node** that maps raw Modbus register/coil addresses to named I/O points. Makes flows more readable by replacing raw addresses with descriptive names.

**When to use:** In large projects with many Modbus points, to maintain a centralized I/O map.

---

## 4. Step-by-Step Exercises

### Exercise A: Read Holding Registers from a Simulated Server

**Goal:** Set up a virtual Modbus server in Node-RED and read data from it — no hardware needed.

**Steps:**

1. **Create the Modbus Server:**
   - Drag a `modbus-server` node onto the workspace
   - Double-click and set:
     - Port: `10502`
     - Coils: `100`
     - Holding Registers: `100`
   - Connect its output to a **Debug** node to see client activity

2. **Create the Reader Flow:**
   - Drag a `modbus-read` node
   - Double-click and configure:
     - **FC:** `FC3: Read Holding Registers`
     - **Address:** `0`
     - **Quantity:** `5`
     - **Poll Rate:** `2` seconds
   - Click the pencil icon next to **Server** to create a new `modbus-client`:
     - Type: `TCP`
     - Host: `127.0.0.1`
     - Port: `10502`
     - Unit ID: `1`
   - Click Add, then Done

3. **View the Results:**
   - Connect `modbus-read` Output 1 → **Debug** node
   - **Deploy** the flow
   - You should see `[0, 0, 0, 0, 0]` in the debug panel (registers start at zero)

4. **Write Data to Test:**
   - Add an **Inject** node with JSON payload: `[100, 200, 300, 400, 500]`
   - Add a `modbus-write` node:
     - FC: `FC16: Write Multiple Registers`
     - Address: `0`
     - Quantity: `5`
     - Server: same `modbus-client` config
   - Connect: `Inject → Modbus Write`
   - **Deploy** and click the Inject button
   - Now the `modbus-read` should show `[100, 200, 300, 400, 500]`!

**Complete Flow Diagram:**

```
┌──────────────────── WRITER SIDE ────────────────────┐
│                                                      │
│  [Inject: [100,200,300,400,500]] ──► [Modbus Write]  │
│                                        FC16, Addr 0  │
│                                                      │
└──────────────────────────────────────────────────────┘
                        │
                        ▼
              [Modbus Server :10502] ──► [Debug: Activity]

                        ▲
                        │
┌──────────────────── READER SIDE ────────────────────┐
│                                                      │
│  [Modbus Read] ──► [Debug: Values]                   │
│    FC3, Addr 0                                       │
│    Qty 5, 2s                                         │
│                                                      │
└──────────────────────────────────────────────────────┘
```

---

### Exercise B: Dynamic Multi-Device Scanner with Flex Getter

**Goal:** Read registers from multiple Modbus device addresses dynamically using `modbus-flex-getter`.

**Steps:**

1. **Set up the Modbus Server** (same as Exercise A, or use a real device)

2. **Create a device list:**
   - Drag an **Inject** node, set payload type to JSON:
   ```json
   [
       {"unitid": 1, "address": 0, "quantity": 5},
       {"unitid": 1, "address": 10, "quantity": 3},
       {"unitid": 1, "address": 20, "quantity": 2}
   ]
   ```

3. **Split and read each device:**
   - Connect `Inject` → **Split** node (splits the array into individual messages)
   - Add a **Function** node after Split:
   ```javascript
   msg.payload = {
       unitid: msg.payload.unitid,
       fc: 3,
       address: msg.payload.address,
       quantity: msg.payload.quantity
   };
   return msg;
   ```
   - Connect `Function` → `modbus-flex-getter` (configured with your server)
   - Connect output → **Debug**

4. **Deploy** and click Inject. You'll see three separate debug messages — one for each address range.

---

### Exercise C: Write Coils (Digital Outputs)

**Goal:** Toggle digital outputs using coil writes (FC5 & FC15).

**Steps:**

1. **Write a single coil ON:**
   - Drag an **Inject** node, set payload to `true` (boolean)
   - Connect to a `modbus-write` node:
     - FC: `FC5: Write Single Coil`
     - Address: `0`
     - Server: your `modbus-client`
   - Clicking Inject sets Coil 0 to ON

2. **Write a single coil OFF:**
   - Another **Inject** with payload `false` → same `modbus-write`

3. **Write multiple coils at once:**
   - **Inject** with JSON payload: `[true, false, true, true, false]`
   - `modbus-write` with FC: `FC15`, Address: `0`, Quantity: `5`

4. **Verify** by reading coils:
   - `modbus-read` with FC: `FC1`, Address: `0`, Quantity: `5`
   - Should show `[1, 0, 1, 1, 0]`

---

### Exercise D: Build a Modbus Data Logger

**Goal:** Poll a Modbus device and log timestamped data to a CSV file.

**Steps:**

1. **Set up the reader:**
   - `modbus-read` node: FC3, Address 0, Quantity 4, Poll Rate 10s

2. **Format as CSV:**
   - Add a **Function** node:
   ```javascript
   let timestamp = new Date().toISOString();
   let values = msg.payload.join(",");
   msg.payload = `${timestamp},${values}\n`;
   return msg;
   ```

3. **Write to file:**
   - Connect to a **File** node (append mode)
   - Set filename to `d:\gitFolders\nodeflows\modbus_log.csv`

4. **Add a CSV header on startup:**
   - Add an **Inject** node set to fire **once after 0.1 seconds**
   - Payload: `timestamp,reg0,reg1,reg2,reg3\n`
   - Connect to the same **File** node

5. **Deploy** and watch the CSV populate!

---

### Exercise E: Modbus-to-HTTP API Bridge

**Goal:** Expose Modbus register data as a REST API endpoint — let any web client read your PLC data.

**Steps:**

1. **Create the HTTP endpoint:**
   - Drag an **HTTP In** node: Method `GET`, URL `/api/modbus/registers`

2. **Read from Modbus on demand:**
   - Connect to a `modbus-getter` node:
     - FC: `FC3`
     - Address: `0`
     - Quantity: `10`
     - Server: your `modbus-client`

> [!CAUTION]
> **Critical step:** Double-click the `modbus-getter` node and enable **"Keep Msg Properties"** (`keepMsgProperties: true`). Without this, the Modbus node will create a brand new `msg` object and **drop `msg.req` and `msg.res`** that the `http in` node attached. The `http response` node needs `msg.res` to send the reply — without it, the browser will hang forever waiting for a response.

3. **Format the response:**
   - Add a **Function** node:
   ```javascript
   msg.payload = {
       timestamp: new Date().toISOString(),
       device: "PLC-01",
       registers: msg.payload,
       status: "ok"
   };
   return msg;
   ```

4. **Send HTTP response:**
   - Connect to an **HTTP Response** node

5. **Deploy** and test: `http://localhost:1880/api/modbus/registers`

**Response example:**
```json
{
    "timestamp": "2026-03-10T12:00:00.000Z",
    "device": "PLC-01",
    "registers": [100, 200, 300, 400, 500, 0, 0, 0, 0, 0],
    "status": "ok"
}
```

---

## 5. Architecture: Serving SCADA and HTTP Simultaneously

A common industrial requirement is to serve **live data to SCADA software** (via Modbus registers) while also exposing the **same data via HTTP/REST APIs** for web dashboards, mobile apps, or AI integrations. The challenge: how do you share live data between these consumers without polling the physical device multiple times?

This section covers four progressively robust approaches — from simplest to industrial-grade.

### Comparison of Approaches

| Approach | Survives Restart? | Historical Data? | Multi-Instance? | Complexity | Best For |
|----------|:-:|:-:|:-:|:-:|----------|
| **Flow Context** | ❌ | ❌ | ❌ | ★☆☆ | Quick prototypes, single flows |
| **Persistent File Context** | ✅ | ❌ | ❌ | ★★☆ | Single-instance, need restart safety |
| **MQTT Broker** | ✅ (retained) | ❌ (without DB) | ✅ | ★★★ | **Production SCADA/IIoT** |
| **SQLite Database** | ✅ | ✅ | ✅ | ★★★ | Data logging, trend analysis, auditing |

---

### 5.1 Approach 1: Flow/Global Context (Simplest)

The simplest pattern — store data in Node-RED's in-memory context.

**Architecture:**

```
[Modbus Read: 2s] ──► [Function: flow.set("liveData")] ──► (stored in memory)
                                                                │
              ┌─────────────────────────────────────────────────┤
              ▼                                                 ▼
  [Inject 1s] ──► [Function: flow.get] ──► [Flex Server]   [HTTP In] ──► [Function: flow.get] ──► [HTTP Response]
                   (push to SCADA registers)                   (serve JSON to web clients)
```

**Data Collection — Function node (runs on Modbus Read output):**

```javascript
let data = {
    timestamp: new Date().toISOString(),
    temperature: msg.payload[0] / 10,
    pressure: msg.payload[1] / 100,
    motorSpeed: msg.payload[2],
    raw: msg.payload
};
flow.set("liveData", data);
return msg;
```

**SCADA Feed — Push to Modbus Flex Server:**

```javascript
let data = flow.get("liveData") || {};
msg.payload = {
    register: "holding",
    address: 0,
    value: [
        Math.round((data.temperature || 0) * 10),
        Math.round((data.pressure || 0) * 100),
        data.motorSpeed || 0
    ]
};
return msg;
```

**HTTP API — Serve to web clients:**

```javascript
let data = flow.get("liveData") || { status: "no data yet" };
msg.payload = data;
return msg;
```

> [!WARNING]
> **Limitation:** Flow context is stored in memory only. All data is **lost on restart**. This is fine for prototyping but not for production.

---

### 5.2 Approach 2: Persistent File Context (Survives Restarts)

Node-RED supports pluggable context stores. By configuring `localfilesystem` in `settings.js`, context data is written to disk and survives restarts.

**Step 1 — Configure `settings.js`:**

Open your `settings.js` (located at `d:\gitFolders\nodeflows\settings.js`) and find the `contextStorage` section. Update it to:

```javascript
contextStorage: {
    default: {
        module: "memory"           // fast, in-memory (volatile)
    },
    persistent: {
        module: "localfilesystem", // saved to disk
        config: {
            dir: "./context-store",     // storage directory
            flushInterval: 10           // write to disk every 10 seconds
        }
    }
}
```

Restart Node-RED after changing `settings.js`.

**Step 2 — Use the persistent store in Function nodes:**

```javascript
// WRITE — specify "persistent" as the store name
let data = {
    timestamp: new Date().toISOString(),
    temperature: msg.payload[0] / 10,
    pressure: msg.payload[1] / 100,
    motorSpeed: msg.payload[2]
};
flow.set("liveData", data, "persistent");
return msg;
```

```javascript
// READ — from persistent store
let data = flow.get("liveData", "persistent") || {};
msg.payload = data;
return msg;
```

> [!NOTE]
> The third argument `"persistent"` tells Node-RED to use the file-backed store instead of the default memory store. Data now survives restarts but is still limited to a single Node-RED instance.

> [!TIP]
> Use `"persistent"` only for data that must survive restarts (config, last-known values). Use the default memory store for high-frequency live data to avoid excessive disk I/O.

---

### 5.3 Approach 3: MQTT Broker (Industrial-Grade, Recommended)

**This is the industry-standard pattern for IIoT/SCADA architectures.** An MQTT broker acts as a central message bus — producers publish data, and any number of consumers subscribe independently.

**Why MQTT is the best choice:**
- **Decoupled** — publishers don't need to know about subscribers
- **Scalable** — add unlimited consumers (SCADA, dashboards, loggers, AI) without touching the producer
- **Retained messages** — new subscribers immediately get the last-known value
- **QoS levels** — guaranteed delivery even on unreliable networks
- **Multi-instance** — multiple Node-RED instances, cloud services, and edge devices can all participate
- **Lightweight** — designed for constrained networks and high-frequency data

**Architecture:**

```
                         ┌──────────────────┐
  [Modbus Read] ──────► │   MQTT Broker     │ ◄──── Other producers
  (publish to topic)     │  (Mosquitto,      │       (sensors, PLCs, etc.)
                         │   HiveMQ, EMQX)   │
                         └──┬───┬───┬───┬───┘
                            │   │   │   │
            ┌───────────────┘   │   │   └──────────────────┐
            ▼                   ▼   ▼                      ▼
   [MQTT Subscribe]     [MQTT Sub] [MQTT Sub]      [MQTT Subscribe]
   Push to Flex Server  HTTP API   Dashboard       Cloud/DB Logger
   (SCADA client reads) (on demand) (live UI)      (InfluxDB, etc.)
```

**Step 1 — Install Mosquitto MQTT Broker (or use any broker):**

```bash
# Windows (using chocolatey)
choco install mosquitto

# Or download from https://mosquitto.org/download/
# Default port: 1883
```

**Step 2 — Publisher Flow (Data Collection):**

```
[Inject: 2s] ──► [Modbus Read FC3] ──► [Function: Format] ──► [MQTT Out]
```

**Function node — Format and prepare for MQTT:**

```javascript
let data = {
    timestamp: new Date().toISOString(),
    temperature: msg.payload[0] / 10,
    pressure: msg.payload[1] / 100,
    motorSpeed: msg.payload[2],
    valveState: msg.payload[3] > 0
};
msg.topic = "plant/line1/plc01/live";
msg.payload = JSON.stringify(data);
return msg;
```

**MQTT Out node config:**
- Server: `localhost:1883`
- Topic: (leave empty — set by `msg.topic`)
- QoS: `1` (at least once delivery)
- Retain: `true` (new subscribers get the last value immediately)

**Step 3 — SCADA Consumer (Modbus Flex Server):**

```
[MQTT In: plant/line1/plc01/live] ──► [Function: Parse + Map] ──► [Modbus Flex Server :10502]
```

```javascript
let data = JSON.parse(msg.payload);
msg.payload = {
    register: "holding",
    address: 0,
    value: [
        Math.round((data.temperature || 0) * 10),
        Math.round((data.pressure || 0) * 100),
        data.motorSpeed || 0,
        data.valveState ? 1 : 0
    ]
};
return msg;
```

SCADA software (Ignition, WinCC, Wonderware) connects to `your-ip:10502` and reads registers normally.

**Step 4 — HTTP API Consumer:**

```
[HTTP In: GET /api/live] ──► [Function: Get Retained] ──► [HTTP Response]
```

For the HTTP API, you have two options:

**Option A — Subscribe and cache (best performance):**

```
[MQTT In: plant/line1/plc01/live] ──► [Function: flow.set("cache", parsed)]
```

Then in the HTTP handler:

```javascript
let data = flow.get("cache") || { status: "waiting for first MQTT message" };
msg.payload = data;
return msg;
```

**Option B — Direct MQTT request-response (simpler, slower):**

Use the retained message feature. Since you published with `retain: true`, any new subscriber immediately gets the last value.

**Step 5 — Topic Structure Best Practice:**

Use a hierarchical topic structure for organized SCADA data:

```
plant/
├── line1/
│   ├── plc01/
│   │   ├── live          ← all registers as JSON
│   │   ├── temperature   ← individual values
│   │   ├── pressure
│   │   └── status
│   └── plc02/
│       └── live
└── line2/
    └── plc01/
        └── live
```

This lets consumers subscribe to exactly what they need:
- `plant/line1/plc01/live` — one specific PLC
- `plant/line1/+/live` — all PLCs on line 1
- `plant/#` — everything in the plant

---

### 5.4 Approach 4: SQLite Database (Persistent + Historical)

When you need **data history** (trend charts, audit logs, reporting), store readings in a database. SQLite is lightweight, requires no separate server, and works well for single-instance setups.

**Install:** Search for `node-red-node-sqlite` in the Palette Manager.

**Step 1 — Create the table (run once):**

```
[Inject: once at start] ──► [Function: CREATE TABLE] ──► [SQLite]
```

```javascript
msg.topic = `CREATE TABLE IF NOT EXISTS modbus_readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    temperature REAL,
    pressure REAL,
    motor_speed INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)`;
return msg;
```

**Step 2 — Insert readings on every poll:**

```
[Modbus Read] ──► [Function: INSERT] ──► [SQLite]
```

```javascript
let temp = msg.payload[0] / 10;
let pressure = msg.payload[1] / 100;
let speed = msg.payload[2];
msg.topic = `INSERT INTO modbus_readings (timestamp, temperature, pressure, motor_speed)
             VALUES ('${new Date().toISOString()}', ${temp}, ${pressure}, ${speed})`;
return msg;
```

**Step 3 — Serve via HTTP API (latest + history):**

```
[HTTP In: GET /api/live] ──► [Function: Query Latest] ──► [SQLite] ──► [HTTP Response]
```

```javascript
// Latest reading
msg.topic = "SELECT * FROM modbus_readings ORDER BY id DESC LIMIT 1";
return msg;
```

```
[HTTP In: GET /api/history] ──► [Function: Query Range] ──► [SQLite] ──► [HTTP Response]
```

```javascript
// Last 100 readings
msg.topic = "SELECT * FROM modbus_readings ORDER BY id DESC LIMIT 100";
return msg;
```

**Step 4 — Feed SCADA from latest DB entry:**

```
[Inject: 1s] ──► [Function: Query] ──► [SQLite] ──► [Function: Map Registers] ──► [Modbus Flex Server]
```

> [!TIP]
> **Combine MQTT + SQLite** for the most robust architecture: MQTT for real-time pub/sub, SQLite (or InfluxDB/TimescaleDB) for historical storage. The MQTT subscriber writes to the database, and the HTTP API queries from it.

---

### 5.5 Recommended Production Architecture

For production SCADA/IIoT systems, **combine MQTT + a time-series database**:

```
[PLCs/Sensors]
      │
      ▼
[Node-RED: Modbus Read] ──► [MQTT Out: plant/line1/plc01/live]
                                            │
                          ┌─────────────────┼─────────────────┐
                          ▼                 ▼                 ▼
                  [MQTT → Flex Server] [MQTT → SQLite]  [MQTT → Cache]
                  (SCADA registers)    (history DB)     (flow.set)
                                                             │
                                                          [HTTP In]
                                                          (REST API)
```

**This gives you:**
- ✅ Single poll of the physical device
- ✅ SCADA gets real Modbus registers
- ✅ HTTP APIs respond instantly from cache
- ✅ Full historical data in the database
- ✅ Survives restarts (MQTT retained + DB)
- ✅ Scales to multiple consumers without touching the producer
- ✅ Future-proof — add cloud, AI, dashboards without redesigning

---

## 6. Troubleshooting

| Problem | Solution |
|---------|----------|
| **Connection refused** | Check IP, port, and firewall rules. Ensure the Modbus device is powered on. |
| **Timeout errors** | Increase the timeout in `modbus-client`. Check cable/network connectivity. |
| **Wrong data values** | Verify zero-based addressing. Register 40001 in docs = address `0`. |
| **Queue overflow** | Reduce poll rate, add `modbus-queue-info` to monitor. |
| **TCP Type issues** | Try switching between "Default", "Telnet", and "TCP-RTU" in the client config. |
| **Unit ID mismatch** | Confirm the slave ID on the physical device matches the `modbus-client` config. |
| **Serial port not found** | Verify COM port number. On Windows, check Device Manager. On Linux, check `/dev/ttyUSB*`. |
| **Data type mismatch** | 16-bit registers may encode 32-bit floats across 2 registers — use a Function node to combine. |

### Decoding 32-bit Float from Two Registers

Many devices store float values across two consecutive 16-bit holding registers. Use this Function node code:

```javascript
// msg.payload = [reg0, reg1] — two 16-bit values
let buf = Buffer.alloc(4);
buf.writeUInt16BE(msg.payload[0], 0);
buf.writeUInt16BE(msg.payload[1], 2);
msg.payload = buf.readFloatBE(0);
return msg;
```

---

## 7. Best Practices

1. **Use `modbus-flex-getter` / `modbus-flex-write`** for production flows — they're more maintainable than hardcoded read/write nodes
2. **Add `modbus-queue-info`** to any flow with multiple polled devices to prevent queue overflow
3. **Set appropriate poll rates** — don't poll faster than the device can respond (typical: 1–10 seconds)
4. **Use `modbus-server`** for development & testing before connecting to real hardware
5. **Group related registers** into single reads (e.g., read 10 registers at once instead of 10 separate single-register reads)
6. **Handle errors** — connect `Catch` nodes to log Modbus communication failures
7. **Use `modbus-io-config`** to create a named I/O map for large installations
8. **Name your nodes** — replace default names like "modbus-read" with descriptive names like "Read Temperature Sensors"

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────┐
│                  MODBUS NODE CHEAT SHEET                │
├─────────────────┬───────────────────────────────────────┤
│ READ (fixed)    │ modbus-read (timer-based polling)     │
│ READ (trigger)  │ modbus-getter (on incoming msg)       │
│ READ (dynamic)  │ modbus-flex-getter (params in msg)    │
├─────────────────┼───────────────────────────────────────┤
│ WRITE (fixed)   │ modbus-write (fixed address)          │
│ WRITE (dynamic) │ modbus-flex-write (params in msg)     │
├─────────────────┼───────────────────────────────────────┤
│ SERVER (fixed)  │ modbus-server (virtual PLC)           │
│ SERVER (dynamic)│ modbus-flex-server (push data in)     │
├─────────────────┼───────────────────────────────────────┤
│ UTILITIES       │ modbus-response (format output)       │
│                 │ modbus-response-filter (filter by ID) │
│                 │ modbus-flex-connector (change conn.)  │
│                 │ modbus-flex-sequencer (multi-read)    │
│                 │ modbus-flex-fc (custom FC)            │
│                 │ modbus-queue-info (queue monitor)     │
│                 │ modbus-io-config (named I/O map)      │
├─────────────────┼───────────────────────────────────────┤
│ CONFIG          │ modbus-client (connection settings)   │
└─────────────────┴───────────────────────────────────────┘
```
