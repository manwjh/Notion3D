"""render-scad endpoint pre-validation."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_render_scad_rejects_absolute_import(client: TestClient, project_id: str):
    res = client.post(
        f"/api/projects/{project_id}/render-scad",
        json={"scad_code": 'import("/tmp/evil.scad");\ncube(10);'},
    )
    assert res.status_code == 400
    assert "绝对路径" in res.json()["detail"]


def test_render_scad_returns_static_wall_warnings(client: TestClient, project_id: str, monkeypatch):
    from app.services import job_service

    async def noop_job(job_id: str) -> None:
        return None

    monkeypatch.setattr(job_service, "run_render_scad_job", noop_job)

    res = client.post(
        f"/api/projects/{project_id}/render-scad",
        json={"scad_code": "wall = 0.5;\ncube(10);"},
    )
    assert res.status_code == 200
    warnings = res.json().get("validation_warnings") or []
    assert any("0.5" in w for w in warnings)
