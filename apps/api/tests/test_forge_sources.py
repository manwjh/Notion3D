"""Forge sources API tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.services import storage


def test_forge_sources_includes_src_files(client: TestClient, project_id: str):
    version_dir = storage.version_dir(project_id, 1)
    version_dir.mkdir(parents=True, exist_ok=True)
    (version_dir / "model.forge.js").write_text(
        "const m = importAssembly('src/motor.forge.js'); return m;",
        encoding="utf-8",
    )
    src_dir = version_dir / "src"
    src_dir.mkdir(parents=True, exist_ok=True)
    (src_dir / "motor.forge.js").write_text("return box(5,5,5);", encoding="utf-8")

    res = client.get(f"/api/projects/{project_id}/versions/1/forge-sources")
    assert res.status_code == 200
    body = res.json()
    assert "importAssembly" in body["forge_code"]
    assert body["files"]["motor.forge.js"] == "return box(5,5,5);"


def test_list_versions_exposes_src_files(client: TestClient, project_id: str):
    storage.update_project_meta(project_id, latest_version=1)

    version_dir = storage.version_dir(project_id, 1)
    version_dir.mkdir(parents=True, exist_ok=True)
    (version_dir / "model.forge.js").write_text("return box(1,1,1);", encoding="utf-8")
    (version_dir / "model.stl").write_text("solid x\nendsolid x\n", encoding="utf-8")
    src_dir = version_dir / "src"
    src_dir.mkdir(parents=True, exist_ok=True)
    (src_dir / "part_a.forge.js").write_text("return sphere(3);", encoding="utf-8")

    res = client.get(f"/api/projects/{project_id}/versions")
    assert res.status_code == 200
    versions = res.json()
    assert len(versions) == 1
    assert versions[0]["src_files"] == ["part_a.forge.js"]
    assert versions[0]["forge_sources_url"].endswith("/forge-sources")


def test_download_src_file(client: TestClient, project_id: str):
    version_dir = storage.version_dir(project_id, 1)
    src_dir = version_dir / "src" / "parts"
    src_dir.mkdir(parents=True, exist_ok=True)
    (version_dir / "model.forge.js").write_text("return box(1,1,1);", encoding="utf-8")
    (src_dir / "gear.forge.js").write_text("return cylinder(10, 5);", encoding="utf-8")

    res = client.get(f"/api/projects/{project_id}/versions/1/src/parts/gear.forge.js")
    assert res.status_code == 200
    assert "cylinder" in res.text


def test_read_src_rejects_traversal(project_id: str):
    from app.services import forgecad_service
    from app.services.cad_types import CadError

    version_dir = storage.version_dir(project_id, 1)
    (version_dir / "model.forge.js").write_text("return box(1,1,1);", encoding="utf-8")

    with pytest.raises(CadError):
        forgecad_service.read_src_file(version_dir, "../model.forge.js")
