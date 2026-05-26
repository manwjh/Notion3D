"""Project state SSE tests."""

from __future__ import annotations

import asyncio
import json

from app.services import project_events


def _parse_sse_data(lines: list[str]) -> list[dict]:
    payloads: list[dict] = []
    for line in lines:
        if line.startswith("data: "):
            payloads.append(json.loads(line.removeprefix("data: ")))
    return payloads


def test_project_events_publish_subscribe():
    async def run() -> None:
        queue = project_events.subscribe("project-1")
        try:
            project_events.notify("project-1")
            received = await asyncio.wait_for(queue.get(), timeout=1.0)
            assert received == "project-1"
        finally:
            project_events.unsubscribe("project-1", queue)

    asyncio.run(run())


def test_project_state_stream_when_agent_idle(client, project_id):
    lines: list[str] = []
    with client.stream("GET", f"/api/projects/{project_id}/state/events") as response:
        assert response.status_code == 200
        for line in response.iter_lines():
            if line:
                lines.append(line)
            if _parse_sse_data(lines):
                break

    payloads = _parse_sse_data(lines)
    assert len(payloads) == 1
    assert payloads[0]["agent"]["active"] is False


def test_project_state_stream_404(client, project_id):
    res = client.get(f"/api/projects/{project_id}/state/events-typo")
    assert res.status_code == 404
