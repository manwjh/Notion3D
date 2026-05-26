"""Design plan assembly_spec (P2) tests."""

from __future__ import annotations

import asyncio
import json

from app.services import design_turn, job_service, storage


def test_design_plan_accepts_assembly_spec(client, project_id):
    design_turn.begin_turn(project_id, "msg-spec", turn_id="turn-spec")

    res = client.post(
        f"/api/projects/{project_id}/design/plan",
        json={
            "turn_id": "turn-spec",
            "task_class": "A",
            "summary": "15 部件打火机",
            "strategy": "from_scratch",
            "assembly_spec": [
                {
                    "id": "CaseShell",
                    "role": "shell",
                    "contains": ["Insert", "Chimney", "FlintWheel"],
                },
                {"id": "Insert", "role": "internal"},
                {"id": "Chimney", "role": "internal"},
                {"id": "FlintWheel", "role": "internal", "anchor": "Chimney"},
                {"id": "LidShell", "role": "lid", "hinge": "CaseShell.left"},
            ],
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body["design_phase"] == "author"
    plan = body["plan"]
    assert plan["modules"] == [
        "CaseShell",
        "Insert",
        "Chimney",
        "FlintWheel",
        "LidShell",
    ]
    assert len(plan["assembly_spec"]) == 5
    assert len(plan["geometry_recipes"]) == 5
    recipes = {r["part_id"]: r["recipe"] for r in plan["geometry_recipes"]}
    assert recipes["CaseShell"] == "sketch_extrude_shell"
    assert recipes["LidShell"] == "sketch_extrude"


def test_design_plan_rejects_invalid_assembly_spec_ref(client, project_id):
    design_turn.begin_turn(project_id, "msg-bad", turn_id="turn-bad")

    res = client.post(
        f"/api/projects/{project_id}/design/plan",
        json={
            "turn_id": "turn-bad",
            "task_class": "A",
            "summary": "坏 plan",
            "strategy": "from_scratch",
            "assembly_spec": [
                {"id": "Shell", "role": "shell", "contains": ["MissingPart"]},
            ],
        },
    )
    assert res.status_code == 422


def test_render_writes_assembly_spec_snapshot(client, project_id, monkeypatch):
    design_turn.begin_turn(project_id, "msg-write", turn_id="turn-write")
    client.post(
        f"/api/projects/{project_id}/design/plan",
        json={
            "turn_id": "turn-write",
            "task_class": "A",
            "summary": "写入 spec",
            "strategy": "from_scratch",
            "assembly_spec": [
                {"id": "Shell", "role": "shell", "contains": ["Motor"]},
                {"id": "Motor", "role": "internal"},
            ],
        },
    )

    captured: dict = {}

    async def fake_render(forge_code, out_dir, **kwargs):
        from app.services.cad_types import RenderResult

        spec_path = out_dir / "assembly_spec.json"
        captured["spec_exists_before_render"] = spec_path.exists()
        if spec_path.exists():
            captured["spec"] = json.loads(spec_path.read_text(encoding="utf-8"))
        (out_dir / "model.stl").write_text("solid x\nendsolid x\n", encoding="utf-8")
        return RenderResult(path=out_dir / "model.stl", warnings=[])

    monkeypatch.setattr(job_service.forgecad_service, "render_forge", fake_render)

    res = client.post(
        f"/api/projects/{project_id}/render-forge",
        json={
            "forge_code": "return box(1,1,1);",
            "label": "spec snapshot",
            "source": "agent",
        },
    )
    assert res.status_code == 200
    job_id = res.json()["id"]

    asyncio.run(job_service.run_render_job(job_id))

    assert captured["spec_exists_before_render"] is True
    assert captured["spec"][0]["id"] == "Shell"
    assert captured["spec"][0]["contains"] == ["Motor"]

    version = job_service.get_job(job_id)["version"]
    version_dir = storage.version_dir(project_id, version)
    assert (version_dir / "assembly_spec.json").exists()
    intent = json.loads((version_dir / "design_intent.json").read_text(encoding="utf-8"))
    assert intent["fidelity"] == "printable"
