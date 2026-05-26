"""MCP client wait_job behavior."""

from __future__ import annotations

from notion3d_mcp.client import Notion3DClient


def test_wait_job_uses_sse_before_polling(monkeypatch, project_id):
    client = Notion3DClient()
    job_id = "job-sse-test"
    terminal = {"id": job_id, "status": "succeeded", "message": "done"}

    monkeypatch.setattr(client, "get_job", lambda pid, jid: {"id": jid, "status": "pending"})
    monkeypatch.setattr(
        client,
        "_wait_job_sse",
        lambda pid, jid, max_wait: terminal if pid == project_id and jid == job_id else None,
    )

    polled: list[str] = []

    def fail_sleep(_seconds: float) -> None:
        polled.append("sleep")
        raise AssertionError("poll fallback should not run when SSE succeeds")

    monkeypatch.setattr("notion3d_mcp.client.time.sleep", fail_sleep)

    result = client.wait_job(project_id, job_id, max_wait=1)
    assert result == terminal
    assert polled == []


def test_wait_job_falls_back_to_polling(monkeypatch, project_id):
    client = Notion3DClient()
    job_id = "job-poll-test"

    states = [
        {"id": job_id, "status": "pending"},
        {"id": job_id, "status": "running"},
        {"id": job_id, "status": "succeeded"},
    ]

    monkeypatch.setattr(client, "get_job", lambda pid, jid: states.pop(0))
    monkeypatch.setattr(client, "_wait_job_sse", lambda pid, jid, max_wait: None)
    monkeypatch.setattr("notion3d_mcp.client.time.sleep", lambda _seconds: None)

    result = client.wait_job(project_id, job_id, max_wait=5, poll_interval=0.01)
    assert result["status"] == "succeeded"
