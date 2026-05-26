"""P3 spatial digest and P4 turn image tests."""

from __future__ import annotations

import base64
import json

from app.services import storage
from app.services.assembly_digest import build_spatial_digest


def test_build_spatial_digest_from_parts_json(project_id):
    version = storage.next_version(project_id)
    out_dir = storage.version_dir(project_id, version)
    parts = {
        "parts": [{"id": "shell", "label": "Shell"}],
        "assembly": {
            "spec": [{"id": "Shell", "role": "shell", "contains": ["Motor"]}],
            "warnings": ["装配校验：Motor 远离装配主体"],
            "bboxes": [
                {
                    "id": "shell",
                    "label": "Shell",
                    "center": [10, 10, 20],
                    "size": [20, 20, 40],
                    "min": [0, 0, 0],
                    "max": [20, 20, 40],
                }
            ],
        },
    }
    (out_dir / "parts.json").write_text(json.dumps(parts), encoding="utf-8")

    digest = build_spatial_digest(project_id, version)
    assert digest is not None
    assert digest["part_count"] == 1
    assert "Shell" in digest["summary"]
    assert digest["review_checklist"]


def test_turn_accepts_image_attachment(client, project_id, monkeypatch):
    from app.services import turn_service

    async def fake_start(project_id: str, pending: dict) -> None:
        return None

    monkeypatch.setattr(turn_service, "finish_agent_run", fake_start)

    captured: dict = {}

    class FakeAdapter:
        id = "bridge"
        title = "fake"
        kind = "http_sidecar"

        def info(self):
            from app.services.agents.base import AgentProviderInfo

            return AgentProviderInfo(id="bridge", title="fake", kind="http", configured=True, ready=True)

        async def info_ready(self):
            return self.info()

        async def start_turn(self, project_id, user_content, **kwargs):
            captured["images"] = kwargs.get("images")
            from app.services.agents.base import AgentSessionHandle

            return AgentSessionHandle(provider="bridge", session_id="s1", run_id="r1")

        async def collect_reply(self, handle):
            return "ok"

        async def run_status(self, handle):
            return "FINISHED"

    async def fake_resolve(*args, **kwargs):
        return FakeAdapter()

    monkeypatch.setattr("app.services.turn_service.resolve_adapter_live", fake_resolve)

    png = base64.b64encode(b"\x89PNG\r\n\x1a\n").decode("ascii")
    res = client.post(
        f"/api/projects/{project_id}/turn",
        json={
            "content": "请看截图",
            "images": [{"data": png, "mime_type": "image/png", "filename": "shot.png"}],
        },
    )
    assert res.status_code == 200

    messages = storage.list_messages(project_id)
    user = next(m for m in messages if m["role"] == "user")
    assert user.get("images")
    assert user["images"][0]["filename"] == "shot.png"
    assert captured.get("images")


def test_message_attachment_route(client, project_id):
    message_id = "msg-img-1"
    saved = storage.project_attachments_dir(project_id, message_id)
    (saved / "shot.png").write_bytes(b"\x89PNG\r\n\x1a\n")

    res = client.get(f"/api/projects/{project_id}/messages/{message_id}/attachments/shot.png")
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("image/")
