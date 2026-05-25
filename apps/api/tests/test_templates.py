"""Template library API."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_list_builtin_forge_templates(client: TestClient):
    res = client.get("/api/templates", params={"scope": "builtin"})
    assert res.status_code == 200
    items = res.json()
    ids = {item["id"] for item in items}
    assert "hello-assembly" in ids
    assert "open-enclosure" in ids


def test_get_forge_template_includes_code(client: TestClient):
    res = client.get("/api/templates/hello-assembly")
    assert res.status_code == 200
    body = res.json()
    assert body["format"] == "forge"
    assert "param(" in body["forge_code"]


def test_apply_forge_template_creates_project(client: TestClient, monkeypatch):
    from app.services import job_service

    async def noop_job(job_id: str) -> None:
        return None

    monkeypatch.setattr(job_service, "run_render_job", noop_job)

    res = client.post(
        "/api/templates/open-enclosure/apply",
        json={"params": {"Outer Width": 70}, "name": "敞口盒测试"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["template_id"] == "open-enclosure"
    assert body["project"]["name"] == "敞口盒测试"
    assert body["job"]["source"] == "template"


def test_save_forge_template_from_version(client: TestClient, project_id: str, monkeypatch):
    from app.config import settings
    from app.services import forgecad_service, storage
    from app.services.cad_types import RenderResult

    async def fake_validate(forge_code: str, out_dir, **kwargs):
        (out_dir / "model.stl").write_text("solid fake\nendsolid fake\n", encoding="utf-8")
        return RenderResult(path=out_dir / "model.stl", warnings=[])

    monkeypatch.setattr(forgecad_service, "validate_forge_render", fake_validate)

    version = 1
    version_dir = storage.version_dir(project_id, version)
    version_dir.mkdir(parents=True, exist_ok=True)
    (version_dir / "model.forge.js").write_text(
        'return box(10,10,10,true);',
        encoding="utf-8",
    )

    save_res = client.post(
        f"/api/projects/{project_id}/versions/{version}/save-template",
        json={
            "id": "my-box",
            "title": "我的盒子",
            "tags": ["测试"],
        },
    )
    assert save_res.status_code == 200
    assert save_res.json()["id"] == "my-box"
    assert (settings.user_templates_dir / "my-box" / "model.forge.js").exists()
