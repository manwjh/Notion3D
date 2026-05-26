#!/usr/bin/env python3
"""End-to-end smoke test: Engine render + optional Web Turn agent."""

from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

API = "http://127.0.0.1:8000"
ROOT = Path(__file__).resolve().parents[1]
POLL_SEC = 2
RENDER_TIMEOUT = 120
TURN_TIMEOUT = 300


def req(method: str, path: str, body: dict | None = None, timeout: float = 60) -> dict:
    url = f"{API}{path}"
    data = None if body is None else json.dumps(body).encode()
    headers = {"Content-Type": "application/json"} if body is not None else {}
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=timeout) as resp:
        raw = resp.read().decode()
        return json.loads(raw) if raw else {}


def wait_job(project_id: str, job_id: str) -> dict:
    deadline = time.time() + RENDER_TIMEOUT
    while time.time() < deadline:
        job = req("GET", f"/api/projects/{project_id}/jobs/{job_id}")
        if job.get("status") in ("succeeded", "failed"):
            return job
        time.sleep(POLL_SEC)
    raise TimeoutError(f"job {job_id} timed out")


def wait_agent(project_id: str) -> dict:
    deadline = time.time() + TURN_TIMEOUT
    last = None
    while time.time() < deadline:
        state = req("GET", f"/api/projects/{project_id}/state")
        last = state
        agent = state.get("agent") or {}
        activity = agent.get("activity") or []
        if activity:
            step = activity[-1]
            print(f"  agent: {step.get('label')} [{step.get('status')}]")
        if not agent.get("active"):
            return state
        time.sleep(POLL_SEC)
    if last and not (last.get("agent") or {}).get("active"):
        return last
    raise TimeoutError("agent turn timed out")


def main() -> int:
    print("== 1. Health ==")
    health = req("GET", "/health")
    assert health.get("status") == "ok", health
    assert health.get("forgecad_available"), "forgecad not available"
    print(f"  forgecad_available={health['forgecad_available']} web_turn={health.get('web_turn')}")

    print("\n== 2. Create project ==")
    project = req("POST", "/api/projects", {"name": "E2E verify"})
    project_id = project["id"]
    print(f"  project_id={project_id}")

    print("\n== 3. Direct render-forge (Engine path) ==")
    forge = """
const bodyW = 36;
const bodyH = 90;
const shellT = 1.8;
const outer = cylinder(bodyH, bodyW / 2, bodyW / 2, 24, true);
const inner = cylinder(bodyH + 2, bodyW / 2 - shellT, bodyW / 2 - shellT, 24, true);
const shell = outer.subtract(inner);
const motor = cylinder(28, 14, 14, 24, true).translate(0, 0, -8);
return [
  { name: "Shell", shape: shell },
  { name: "Motor", shape: motor },
];
"""
    job = req(
        "POST",
        f"/api/projects/{project_id}/render-forge",
        {"forge_code": forge, "label": "e2e-car-parts", "source": "manual"},
    )
    job_id = job["id"]
    print(f"  job_id={job_id}")
    done = wait_job(project_id, job_id)
    assert done["status"] == "succeeded", done
    version = done.get("version")
    print(f"  render OK version={version} stl_ready={done.get('stl_ready')}")

    versions = req("GET", f"/api/projects/{project_id}/versions")
    assert any(v.get("version") == version for v in versions), versions
    print(f"  versions={len(versions)}")

    print("\n== 3b. Constrained sketch render (WASM solver) ==")
    sketch_path = ROOT / "templates" / "builtin" / "sketch-enclosure" / "model.forge.js"
    sketch_forge = sketch_path.read_text(encoding="utf-8")
    sketch_job = req(
        "POST",
        f"/api/projects/{project_id}/render-forge",
        {"forge_code": sketch_forge, "label": "e2e-sketch-enclosure", "source": "manual"},
    )
    sketch_done = wait_job(project_id, sketch_job["id"])
    assert sketch_done["status"] == "succeeded", sketch_done
    print(f"  sketch render OK version={sketch_done.get('version')} stl_ready={sketch_done.get('stl_ready')}")

    print("\n== 4. Web Turn (Agent + MCP path) ==")
    if health.get("web_turn_ready") and health.get("web_chat_mode") == "agent":
        turn = req(
            "POST",
            f"/api/projects/{project_id}/turn",
            {"content": "做一个边长 25mm 的立方体，直接 render，不用长篇解释。"},
        )
        assert turn.get("routing") == "agent", turn
        print(f"  turn_id={turn.get('turn_id')} routing=agent")
        final = wait_agent(project_id)
        msgs = final.get("messages") or []
        assistant = [m for m in msgs if m.get("role") == "assistant"]
        assert assistant, "no assistant reply"
        print(f"  messages={len(msgs)} assistant_replies={len(assistant)}")
        activity = (final.get("agent") or {}).get("activity") or []
        if activity:
            print(f"  activity_steps={len(activity)}")
        v2 = req("GET", f"/api/projects/{project_id}/versions")
        print(f"  versions_after_agent={len(v2)}")
    else:
        print("  SKIP (web_turn not ready)")

    print("\n== PASS: full flow verified ==")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (urllib.error.URLError, TimeoutError, AssertionError) as exc:
        print(f"\n== FAIL: {exc} ==", file=sys.stderr)
        raise SystemExit(1)
