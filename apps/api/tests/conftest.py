"""Shared API test fixtures."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    from pathlib import Path

    from app.config import settings

    data_dir = tmp_path / "data"
    data_dir.mkdir()
    monkeypatch.setattr(settings, "data_dir", data_dir)
    repo_root = Path(__file__).resolve().parents[3]
    monkeypatch.setattr(settings, "templates_dir", repo_root / "templates")

    from app.main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def project_id(client: TestClient) -> str:
    res = client.post("/api/projects", json={"name": "测试项目"})
    assert res.status_code == 201
    return res.json()["id"]
