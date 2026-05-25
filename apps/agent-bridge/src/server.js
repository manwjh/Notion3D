/**
 * Notion3D ↔ @cursor/sdk local runtime bridge (HTTP).
 * Not Cursor IDE — programmatic local agents with notion3d MCP.
 */

const http = require("http");
const path = require("path");
const { randomUUID } = require("crypto");
const { Agent, Cursor } = require("@cursor/sdk");

const PORT = Number(process.env.NOTION3D_AGENT_BRIDGE_PORT || 8787);
const REPO_ROOT =
  process.env.NOTION3D_REPO_ROOT || path.resolve(__dirname, "../../..");
const API_KEY = process.env.CURSOR_API_KEY || "";
const MODEL = process.env.NOTION3D_CURSOR_MODEL || "composer-2.5";
const MCP_PYTHON =
  process.env.NOTION3D_PYTHON || process.env.PYTHON || "python3.11";
const MCP_MODULE = process.env.NOTION3D_MCP_MODULE || "notion3d_mcp.server";

/** @type {Map<string, import("@cursor/sdk").SDKAgent>} */
const agents = new Map();

/** @type {Map<string, { status: string, result?: string, error?: string, done: Promise<void> }>} */
const runs = new Map();

function mcpServers() {
  const command =
    process.env.NOTION3D_MCP_COMMAND || MCP_PYTHON;
  const args = process.env.NOTION3D_MCP_COMMAND
    ? undefined
    : ["-m", MCP_MODULE];
  const server = {
    type: "stdio",
    command,
    env: {
      NOTION3D_API_BASE:
        process.env.NOTION3D_API_BASE || "http://127.0.0.1:8000",
      NOTION3D_WEB_BASE:
        process.env.NOTION3D_WEB_BASE || "http://localhost:5173",
    },
  };
  if (args) {
    server.args = args;
  }
  return {
    notion3d: server,
  };
}

function baseOptions(logicalId) {
  return {
    apiKey: API_KEY,
    agentId: logicalId,
    name: `Notion3D ${logicalId}`,
    model: { id: MODEL },
    instructions:
      "You are the Notion3D design agent. Follow project Skills in order: " +
      "notion3d-intake → notion3d-plan → notion3d-forge-author → notion3d-mcp → notion3d-review. " +
      "Before render_forge: notion3d_report_design_plan. After wait_job: notion3d_report_design_review. " +
      "Default from_scratch or edit previous model.forge.js; list_templates only for demo templates.",
    local: {
      cwd: REPO_ROOT,
      settingSources: ["project"],
    },
    mcpServers: mcpServers(),
  };
}

async function getOrCreateAgent(logicalId) {
  const cached = agents.get(logicalId);
  if (cached) return cached;

  let agent;
  try {
    agent = await Agent.resume(logicalId, baseOptions(logicalId));
  } catch {
    agent = await Agent.create(baseOptions(logicalId));
  }
  agents.set(logicalId, agent);
  return agent;
}

function collectAssistantText(event, parts) {
  if (event.type !== "assistant") return;
  for (const block of event.message.content) {
    if (block.type === "text" && block.text) parts.push(block.text);
  }
}

async function executeRun(logicalId, prompt, runId) {
  const entry = { status: "RUNNING", result: undefined, error: undefined };
  entry.done = (async () => {
    try {
      const agent = await getOrCreateAgent(logicalId);
      agents.set(logicalId, agent);

      let run;
      try {
        run = await agent.send(prompt);
      } catch (err) {
        if (err?.code === "agent_busy" || err?.name === "AgentBusyError") {
          run = await agent.send(prompt, { local: { force: true } });
        } else {
          throw err;
        }
      }

      const parts = [];
      for await (const event of run.stream()) {
        collectAssistantText(event, parts);
      }
      const outcome = await run.wait();
      const text = (outcome.result || parts.join("")).trim();
      entry.result = text;
      entry.status =
        outcome.status === "finished"
          ? "FINISHED"
          : String(outcome.status || "finished").toUpperCase();
    } catch (err) {
      entry.status = "ERROR";
      entry.error = err?.message || String(err);
    }
  })();
  runs.set(runId, entry);
  await entry.done;
}

function readJson(req) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    req.on("data", (c) => chunks.push(c));
    req.on("end", () => {
      try {
        const raw = Buffer.concat(chunks).toString("utf8");
        resolve(raw ? JSON.parse(raw) : {});
      } catch (err) {
        reject(err);
      }
    });
    req.on("error", reject);
  });
}

function sendJson(res, status, body) {
  res.writeHead(status, { "Content-Type": "application/json" });
  res.end(JSON.stringify(body));
}

async function handleHealth(_req, res) {
  let keyOk = false;
  if (API_KEY) {
    try {
      await Cursor.me({ apiKey: API_KEY });
      keyOk = true;
    } catch {
      keyOk = false;
    }
  }
  sendJson(res, 200, {
    status: "ok",
    runtime: "cursor_sdk_local",
    cursor_api_key: Boolean(API_KEY),
    cursor_api_ready: keyOk,
    repo_root: REPO_ROOT,
    model: MODEL,
    mcp_python: MCP_PYTHON,
    mcp_module: MCP_MODULE,
  });
}

async function handleTurn(req, res) {
  const body = await readJson(req);
  const logicalId = String(body.agentId || body.agent_id || "").trim();
  const prompt = String(body.prompt || "").trim();
  if (!logicalId || !prompt) {
    sendJson(res, 400, { error: "agentId and prompt are required" });
    return;
  }
  if (!API_KEY) {
    sendJson(res, 503, { error: "CURSOR_API_KEY not configured" });
    return;
  }

  const runId = randomUUID();
  void executeRun(logicalId, prompt, runId);
  sendJson(res, 202, {
    agentId: logicalId,
    runId,
    status: "RUNNING",
  });
}

async function handleRunStatus(_req, res, runId) {
  const entry = runs.get(runId);
  if (!entry) {
    sendJson(res, 404, { error: "run not found" });
    return;
  }
  sendJson(res, 200, {
    runId,
    status: entry.status,
    result: entry.result,
    error: entry.error,
  });
}

async function handleRunWait(_req, res, runId) {
  const entry = runs.get(runId);
  if (!entry) {
    sendJson(res, 404, { error: "run not found" });
    return;
  }
  await entry.done;
  sendJson(res, 200, {
    runId,
    status: entry.status,
    result: entry.result,
    error: entry.error,
  });
}

const server = http.createServer(async (req, res) => {
  try {
    const url = new URL(req.url || "/", `http://127.0.0.1:${PORT}`);
    if (req.method === "GET" && url.pathname === "/health") {
      await handleHealth(req, res);
      return;
    }
    if (req.method === "POST" && url.pathname === "/v1/turn") {
      await handleTurn(req, res);
      return;
    }
    const runMatch = url.pathname.match(/^\/v1\/runs\/([^/]+)$/);
    if (req.method === "GET" && runMatch) {
      await handleRunStatus(req, res, runMatch[1]);
      return;
    }
    const waitMatch = url.pathname.match(/^\/v1\/runs\/([^/]+)\/wait$/);
    if (req.method === "GET" && waitMatch) {
      await handleRunWait(req, res, waitMatch[1]);
      return;
    }
    sendJson(res, 404, { error: "not found" });
  } catch (err) {
    sendJson(res, 500, { error: err?.message || String(err) });
  }
});

server.listen(PORT, "127.0.0.1", () => {
  console.log(`notion3d-agent-bridge http://127.0.0.1:${PORT} (sdk local)`);
});
