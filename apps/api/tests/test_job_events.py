"""Job SSE stream tests."""

from __future__ import annotations

import asyncio
import json

from app.services import job_events, job_service


def _parse_sse_data(lines: list[str]) -> list[dict]:
    payloads: list[dict] = []
    for line in lines:
        if line.startswith("data: "):
            payloads.append(json.loads(line.removeprefix("data: ")))
    return payloads


def test_job_events_publish_subscribe():
    async def run() -> None:
        queue = job_events.subscribe("job-1")
        try:
            job_events.publish({"id": "job-1", "status": "running", "message": "working"})
            received = await asyncio.wait_for(queue.get(), timeout=1.0)
            assert received["status"] == "running"
        finally:
            job_events.unsubscribe("job-1", queue)

    asyncio.run(run())


def test_job_events_publish_prefers_terminal_on_full_queue():
    async def run() -> None:
        queue = job_events.subscribe("job-full")
        try:
            while True:
                try:
                    queue.put_nowait({"id": "job-full", "status": "running"})
                except asyncio.QueueFull:
                    break
            job_events.publish({"id": "job-full", "status": "succeeded", "message": "done"})
            received = await asyncio.wait_for(queue.get(), timeout=1.0)
            assert received["status"] == "succeeded"
        finally:
            job_events.unsubscribe("job-full", queue)

    asyncio.run(run())


def test_job_events_stream_returns_terminal_job(client, project_id):
    job = job_service.create_render_job(
        project_id,
        "export default cube();",
        label="SSE terminal",
    )
    job_service.update_job(job["id"], status="succeeded", message="done", version=1)

    lines: list[str] = []
    with client.stream(
        "GET",
        f"/api/projects/{project_id}/jobs/{job['id']}/events",
    ) as response:
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")
        for line in response.iter_lines():
            if line:
                lines.append(line)

    payloads = _parse_sse_data(lines)
    assert len(payloads) >= 1
    assert payloads[-1]["status"] == "succeeded"


def test_job_events_stream_404_for_unknown_job(client, project_id):
    res = client.get(f"/api/projects/{project_id}/jobs/missing-job/events")
    assert res.status_code == 404
