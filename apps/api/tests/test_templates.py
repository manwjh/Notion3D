"""Template library API."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_list_builtin_templates(client: TestClient):
    res = client.get("/api/templates", params={"scope": "builtin"})
    assert res.status_code == 200
    items = res.json()
    ids = {item["id"] for item in items}
    assert "parametric-cube" in ids
    assert "phone-stand" in ids
    assert "gear-pair-10-1" in ids
    assert "cable-clip" in ids
    assert "sd-card-box" in ids
    assert len(items) >= 8


def test_get_template_includes_scad(client: TestClient):
    res = client.get("/api/templates/parametric-cube")
    assert res.status_code == 200
    body = res.json()
    assert body["title"] == "参数化立方体"
    assert "cube(" in body["scad_code"]


def test_apply_template_creates_project(client: TestClient):
    res = client.post(
        "/api/templates/parametric-cube/apply",
        json={"params": {"size": 30}, "name": "立方体测试"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["template_id"] == "parametric-cube"
    assert body["project"]["name"] == "立方体测试"
    assert body["job"]["project_id"] == body["project"]["id"]
    assert body["job"]["source"] == "template"


def test_apply_template_to_existing_project(client: TestClient, project_id: str):
    res = client.post(
        "/api/templates/parametric-cube/apply",
        json={"project_id": project_id, "params": {"size": 25}},
    )
    assert res.status_code == 200
    assert res.json()["project"]["id"] == project_id


def test_save_template_from_version(client: TestClient, project_id: str):
    from app.config import settings
    from app.services import storage

    version = 1
    version_dir = storage.version_dir(project_id, version)
    version_dir.mkdir(parents=True, exist_ok=True)
    (version_dir / "model.scad").write_text(
        "size = 22;\ncube(size);\n",
        encoding="utf-8",
    )

    save_res = client.post(
        f"/api/projects/{project_id}/versions/{version}/save-template",
        json={
            "id": "my-cube",
            "title": "我的立方体",
            "tags": ["测试"],
        },
    )
    assert save_res.status_code == 200
    assert save_res.json()["id"] == "my-cube"
    assert (settings.user_templates_dir / "my-cube" / "model.scad").exists()

    listed = client.get("/api/templates", params={"scope": "user"}).json()
    assert any(item["id"] == "my-cube" for item in listed)
