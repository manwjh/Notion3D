"""ForgeCAD render endpoint tests."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_render_forge_rejects_empty(client: TestClient, project_id: str):
    res = client.post(
        f"/api/projects/{project_id}/render-forge",
        json={"forge_code": "   "},
    )
    assert res.status_code == 400


def test_render_forge_accepts_code(client: TestClient, project_id: str, monkeypatch):
    from app.services import job_service

    async def noop_job(job_id: str) -> None:
        return None

    monkeypatch.setattr(job_service, "run_render_job", noop_job)

    res = client.post(
        f"/api/projects/{project_id}/render-forge",
        json={"forge_code": 'return box(10,10,10,true);'},
    )
    assert res.status_code == 200
    assert res.json()["status"] == "pending"


def test_render_forge_accepts_src_files(client: TestClient, project_id: str, monkeypatch):
    from app.services import job_service

    captured: list[dict] = []
    real_create = job_service.create_render_job

    def spy_create(*args, **kwargs):
        captured.append(kwargs)
        return real_create(*args, **kwargs)

    async def noop_job(job_id: str) -> None:
        return None

    monkeypatch.setattr(job_service, "create_render_job", spy_create)
    monkeypatch.setattr(job_service, "run_render_job", noop_job)

    res = client.post(
        f"/api/projects/{project_id}/render-forge",
        json={
            "forge_code": "const m = importAssembly('src/motor.forge.js'); return m;",
            "files": {"motor.forge.js": "return box(5,5,5);"},
        },
    )
    assert res.status_code == 200
    assert captured[0].get("forge_files") == {"motor.forge.js": "return box(5,5,5);"}
