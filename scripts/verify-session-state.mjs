/**
 * Quick checks for workbench session busy-state logic (no browser).
 * Run: node scripts/verify-session-state.mjs
 */

function mergeSessionPhase(generation, agentBusy, activeTurn, agentActive = false) {
  const designPhase = activeTurn?.design_phase ?? null;
  if (generation?.busy) {
    const terminal = generation.phase === "done" || generation.phase === "failed";
    return {
      phase: generation.phase,
      detail: generation.detail,
      busy: !terminal,
      lane: terminal ? "idle" : "render",
      designPhase,
    };
  }
  if (agentBusy || agentActive) {
    return {
      phase: "generating",
      detail: "正在建模…",
      busy: true,
      lane: "agent",
      designPhase: designPhase ?? "author",
    };
  }
  return {
    phase: generation?.phase ?? "idle",
    detail: generation?.detail ?? null,
    busy: false,
    lane: "idle",
    designPhase,
  };
}

function jobBusy(generation) {
  const g = generation;
  if (!g?.busy) return false;
  if (g.phase === "done" || g.phase === "failed") return false;
  if (g.stlReady) return false;
  return true;
}

function inFlightVersion(followLatest, jobVersion, generation) {
  if (!followLatest || jobVersion == null) return null;
  const g = generation;
  if (!g) return null;
  if (jobBusy(g) || g.stlReady) return jobVersion;
  return null;
}

const turn = {
  id: "t1",
  agent_phase: "running",
  render_phase: "running",
  design_phase: "render",
  user_message_id: "u1",
};

const cases = [
  {
    name: "stale render_phase without generation is not busy",
    ok: !mergeSessionPhase(null, false, turn).busy,
  },
  {
    name: "stale agent_phase alone is not busy",
    ok: !mergeSessionPhase(null, false, { ...turn, render_phase: "idle" }).busy,
  },
  {
    name: "agentActive shows agent busy",
    ok: mergeSessionPhase(null, false, null, true).busy,
  },
  {
    name: "stlReady clears jobBusy while generation still exists",
    ok: !jobBusy({
      phase: "rendering",
      busy: true,
      stlReady: true,
      version: 2,
    }),
  },
  {
    name: "stlReady keeps inFlightVersion for left panel URLs",
    ok:
      inFlightVersion(
        true,
        2,
        { phase: "rendering", busy: true, stlReady: true, version: 2 },
      ) === 2,
  },
  {
    name: "done generation is not busy in chat",
    ok: !mergeSessionPhase(
      { phase: "done", detail: "ok", busy: true, version: 2 },
      false,
      null,
    ).busy,
  },
  {
    name: "active render tracking stays busy",
    ok: mergeSessionPhase(
      { phase: "rendering", detail: "x", busy: true, version: 2 },
      false,
      null,
    ).busy,
  },
];

let failed = 0;
for (const c of cases) {
  if (c.ok) console.log("OK:", c.name);
  else {
    console.error("FAIL:", c.name);
    failed++;
  }
}

if (failed) process.exit(1);
console.log(`\n${cases.length} session-state checks passed.`);
