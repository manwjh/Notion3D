"""Assembly spatial validation and render-first auto-pass."""

from __future__ import annotations

from app.services import design_turn, forgecad_service, job_store, storage


def test_forge_export_summary_parses_assembly_warnings():
    summary = forgecad_service._parse_summary(
        'noise\n{"objects": 5, "assembly_warnings": ["装配校验：A 远离装配主体"]}\n'
    )
    assert summary.objects == 5
    assert summary.assembly_warnings == ["装配校验：A 远离装配主体"]


def test_auto_pass_with_advisory_assembly_warnings(client, project_id):
    design_turn.begin_turn(project_id, "msg-asm", turn_id="turn-asm")
    design_turn.ensure_implicit_plan(project_id, "turn-asm", "测试装配")
    design_turn.register_job(project_id, "turn-asm", "job-asm", prompt="测试装配")
    job_store.save_job(
        {
            "id": "job-asm",
            "project_id": project_id,
            "turn_id": "turn-asm",
            "status": "succeeded",
            "version": 1,
            "kind": "render",
            "prompt": "测试装配",
            "validation_warnings": ["装配校验：FlintWheel 远离装配主体（42.0mm），可能 translate 坐标错误"],
            "created_at": "2026-01-01T00:00:00+00:00",
            "updated_at": "2026-01-01T00:00:01+00:00",
        }
    )

    design_turn.sync_render_from_job(
        project_id,
        {
            "id": "job-asm",
            "turn_id": "turn-asm",
            "status": "succeeded",
            "version": 1,
        },
    )
    design_turn.set_agent_replied(project_id, "turn-asm", "asst-asm")

    assert design_turn.get_active_turn(project_id) is None
    messages = storage.list_messages(project_id)
    assert not any("装配校验未通过" in m.get("content", "") for m in messages)


def test_auto_pass_with_advisory_capability_warnings(client, project_id):
    design_turn.begin_turn(project_id, "msg-vis", turn_id="turn-vis")
    design_turn.ensure_implicit_plan(project_id, "turn-vis", "逼真打火机")
    design_turn.register_job(project_id, "turn-vis", "job-vis", prompt="逼真打火机")
    job_store.save_job(
        {
            "id": "job-vis",
            "project_id": project_id,
            "turn_id": "turn-vis",
            "status": "succeeded",
            "version": 1,
            "kind": "render",
            "prompt": "逼真打火机",
            "validation_warnings": [
                "建模建议：部件 CaseShell 计划为「草图拉伸空心壳」，脚本未检测到 constrainedSketch、extrude"
            ],
            "created_at": "2026-01-01T00:00:00+00:00",
            "updated_at": "2026-01-01T00:00:01+00:00",
        }
    )

    design_turn.sync_render_from_job(
        project_id,
        {
            "id": "job-vis",
            "turn_id": "turn-vis",
            "status": "succeeded",
            "version": 1,
        },
    )
    design_turn.set_agent_replied(project_id, "turn-vis", "asst-vis")

    assert design_turn.get_active_turn(project_id) is None


def test_auto_pass_still_works_without_assembly_warnings(client, project_id):
    design_turn.begin_turn(project_id, "msg-ok", turn_id="turn-ok")
    design_turn.ensure_implicit_plan(project_id, "turn-ok", "测试立方体")
    design_turn.register_job(project_id, "turn-ok", "job-ok", prompt="测试立方体")
    job_store.save_job(
        {
            "id": "job-ok",
            "project_id": project_id,
            "turn_id": "turn-ok",
            "status": "succeeded",
            "version": 1,
            "kind": "render",
            "prompt": "测试立方体",
            "validation_warnings": ["ForgeCAD 导出 5 个部件，复杂装配建议 ≥3 个命名 part"],
            "created_at": "2026-01-01T00:00:00+00:00",
            "updated_at": "2026-01-01T00:00:01+00:00",
        }
    )

    design_turn.set_agent_replied(project_id, "turn-ok", "asst-ok")
    design_turn.sync_render_from_job(
        project_id,
        {
            "id": "job-ok",
            "turn_id": "turn-ok",
            "status": "succeeded",
            "version": 1,
        },
    )

    assert design_turn.get_active_turn(project_id) is None
    messages = storage.list_messages(project_id)
    assert not any("装配校验未通过" in m.get("content", "") for m in messages)
