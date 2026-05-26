/**
 * Notion3D Web Turn bridge — HTTP sidecar to local agent runtime + notion3d MCP.
 * Uses @cursor/sdk programmatically (not Cursor IDE).
 */

const http = require("http");
const path = require("path");
const { randomUUID } = require("crypto");
const { Agent, Cursor } = require("@cursor/sdk");
const { createActivityCollector } = require("./activity");

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
      "You are the Notion3D modeling partner. Render-first: health → render_forge → wait_job → iterate from spatial_digest and validation_warnings (advisory only). Read docs/forge-modeling-guide.md. Optional: report_design_plan / report_design_review to archive decisions. Full ForgeCAD API available; templates are shortcuts. Do not expose pipeline jargon to the user.",
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

async function executeRun(logicalId, prompt, runId, images) {
  const activityCollector = createActivityCollector();
  const entry = {
    status: "RUNNING",
    result: undefined,
    error: undefined,
    activity: activityCollector.snapshot(),
  };
  entry.done = (async () => {
    try {
      const agent = await getOrCreateAgent(logicalId);
      agents.set(logicalId, agent);

      const message =
        Array.isArray(images) && images.length > 0
          ? {
              text: prompt,
              images: images.map((img) => ({
                data: String(img.data || ""),
                mimeType: String(img.mimeType || img.mime_type || "image/png"),
              })),
            }
          : prompt;

      activityCollector.ingest({ type: "status", message: "Agent 开始处理…" });

      let run;
      try {
        run = await agent.send(message);
      } catch (err) {
        if (err?.code === "agent_busy" || err?.name === "AgentBusyError") {
          run = await agent.send(message, { local: { force: true } });
        } else {
          throw err;
        }
      }

      const parts = [];
      for await (const event of run.stream()) {
        activityCollector.ingest(event);
        entry.activity = activityCollector.snapshot();
        collectAssistantText(event, parts);
      }
      const outcome = await run.wait();
      entry.activity = activityCollector.snapshot();
      const text = (outcome.result || parts.join("")).trim();
      entry.result = text;
      entry.status =
        outcome.status === "finished"
          ? "FINISHED"
          : String(outcome.status || "finished").toUpperCase();
    } catch (err) {
      entry.status = "ERROR";
      entry.error = err?.message || String(err);
      activityCollector.ingest({
        type: "status",
        message: `出错：${entry.error}`,
      });
      entry.activity = activityCollector.snapshot();
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

/** Cached Cursor.me — avoid blocking every Engine/SSE health probe. */
let keyVerifyCache = { ok: false, at: 0 };
const KEY_VERIFY_TTL_MS = 120_000;
let keyVerifyInFlight = null;

async function verifyApiKey() {
  if (!API_KEY) {
    keyVerifyCache = { ok: false, at: Date.now() };
    return false;
  }
  const now = Date.now();
  if (now - keyVerifyCache.at < KEY_VERIFY_TTL_MS) {
    return keyVerifyCache.ok;
  }
  if (keyVerifyInFlight) {
    return keyVerifyInFlight;
  }
  keyVerifyInFlight = (async () => {
    try {
      await Cursor.me({ apiKey: API_KEY });
      keyVerifyCache = { ok: true, at: Date.now() };
      return true;
    } catch {
      keyVerifyCache = { ok: false, at: Date.now() };
      return false;
    } finally {
      keyVerifyInFlight = null;
    }
  })();
  return keyVerifyInFlight;
}

async function handleHealth(_req, res) {
  const configured = Boolean(API_KEY);
  const keyVerified = configured ? await verifyApiKey() : false;
  sendJson(res, 200, {
    status: "ok",
    runtime: "bridge",
    api_key_configured: configured,
    api_key_verified: keyVerified,
    api_ready: configured,
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
  const images = Array.isArray(body.images) ? body.images : [];
  if (!logicalId || !prompt) {
    sendJson(res, 400, { error: "agentId and prompt are required" });
    return;
  }
  if (!API_KEY) {
    sendJson(res, 503, { error: "CURSOR_API_KEY not configured" });
    return;
  }

  const runId = randomUUID();
  void executeRun(logicalId, prompt, runId, images);
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
    activity: entry.activity || [],
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
    activity: entry.activity || [],
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
  console.log(`notion3d-agent-bridge http://127.0.0.1:${PORT} (web turn bridge)`);
});
