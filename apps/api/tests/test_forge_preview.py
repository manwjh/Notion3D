"""Forge preview API tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.services import storage


def test_forge_preview_requires_forge_source(client: TestClient, project_id: str, monkeypatch):
    from app.services import forge_preview_service

    async def fake_ensure(*_args, **_kwargs):
        return {
            "ready": True,
            "url": "http://127.0.0.1:5174/",
            "embed_url": "/forge-preview/",
            "error": None,
            "mode": "studio",
            "port": 5174,
        }

    monkeypatch.setattr(forge_preview_service, "ensure_preview", fake_ensure)

    version_dir = storage.version_dir(project_id, 1)
    version_dir.mkdir(parents=True, exist_ok=True)
    (version_dir / "model.forge.js").write_text("return box(1,1,1);", encoding="utf-8")

    res = client.post(f"/api/projects/{project_id}/versions/1/forge-preview")
    assert res.status_code == 200
    body = res.json()
    assert body["ready"] is True
    assert body["embed_url"] == "/forge-preview/"


def test_forge_preview_missing_source(client: TestClient, project_id: str, monkeypatch):
    from app.services import forge_preview_service

    async def fake_fail(*_args, **_kwargs):
        return {"ready": False, "url": None, "embed_url": None, "error": "该版本没有 Forge 源码"}

    monkeypatch.setattr(forge_preview_service, "ensure_preview", fake_fail)

    res = client.post(f"/api/projects/{project_id}/versions/1/forge-preview")
    assert res.status_code == 503
