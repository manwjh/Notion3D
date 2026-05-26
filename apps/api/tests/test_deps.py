"""Project dependency tests."""

from notion3d_mcp.client import Notion3DClient


def test_wait_agent_uses_sse_before_polling(monkeypatch, project_id):
    client = Notion3DClient()
    terminal = {
        "agent": {"active": False},
        "messages": [],
    }

    monkeypatch.setattr(
        client,
        "get_project_state",
        lambda pid: {"agent": {"active": True}, "messages": []},
    )
    monkeypatch.setattr(
        client,
        "_wait_project_state_sse",
        lambda pid, max_wait: terminal if pid == project_id else None,
    )
    monkeypatch.setattr(
        "notion3d_mcp.client.time.sleep",
        lambda _seconds: (_ for _ in ()).throw(AssertionError("poll fallback")),
    )

    result = client.wait_agent(project_id, max_wait=1)
    assert result == terminal


def test_get_project_or_404(client, project_id):
    ok = client.get(f"/api/projects/{project_id}")
    assert ok.status_code == 200

    missing = client.get("/api/projects/missing-project-id")
    assert missing.status_code == 404
