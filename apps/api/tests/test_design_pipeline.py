"""Design pipeline plan/review API and turn phases."""

from __future__ import annotations

from app.services import design_turn, storage


def test_design_plan_advances_to_author(client, project_id):
    design_turn.begin_turn(project_id, "msg-1", turn_id="turn-1")

    res = client.post(
        f"/api/projects/{project_id}/design/plan",
        json={
            "turn_id": "turn-1",
            "task_class": "A",
            "summary": "40mm 参数化立方体",
            "strategy": "from_scratch",
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body["design_phase"] == "author"
    assert body["plan"]["summary"] == "40mm 参数化立方体"


def test_design_plan_class_c_still_authoring(client, project_id):
    design_turn.begin_turn(project_id, "msg-2", turn_id="turn-2")

    res = client.post(
        f"/api/projects/{project_id}/design/plan",
        json={
            "turn_id": "turn-2",
            "task_class": "C",
            "summary": "卡通角色简模",
            "strategy": "from_scratch",
        },
    )
    assert res.status_code == 200
    assert res.json()["design_phase"] == "author"


def test_design_plan_chat_only_marks_done(client, project_id):
    design_turn.begin_turn(project_id, "msg-3", turn_id="turn-3")

    res = client.post(
        f"/api/projects/{project_id}/design/plan",
        json={
            "turn_id": "turn-3",
            "task_class": "A",
            "summary": "用户问如何使用工作台",
            "strategy": "chat_only",
        },
    )
    assert res.status_code == 200
    assert res.json()["design_phase"] == "done"


def test_design_review_pass_finalizes(client, project_id):
    design_turn.begin_turn(project_id, "msg-4", turn_id="turn-4")
    design_turn._patch_turn(
        project_id,
        design_phase="review",
        render_phase="done",
        job_ids=["j1"],
        agent_phase="replied",
    )

    res = client.post(
        f"/api/projects/{project_id}/design/review",
        json={
            "turn_id": "turn-4",
            "status": "pass",
            "notes": ["尺寸符合 plan"],
        },
    )
    assert res.status_code == 200
    assert res.json()["design_phase"] == "done"
    assert design_turn.get_active_turn(project_id) is None


def test_design_review_retry_back_to_plan(client, project_id):
    design_turn.begin_turn(project_id, "msg-5", turn_id="turn-5")
    design_turn._patch_turn(project_id, design_phase="review", render_phase="done", job_ids=["j1"])

    res = client.post(
        f"/api/projects/{project_id}/design/review",
        json={
            "turn_id": "turn-5",
            "status": "retry",
            "retry_phase": "plan",
            "notes": ["应改用模板"],
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body["design_phase"] == "plan"
    assert body["revision"] == 1


def test_get_design_state(client, project_id):
    design_turn.begin_turn(project_id, "msg-6", turn_id="turn-6")
    empty = client.get(f"/api/projects/{project_id}/design/state")
    assert empty.status_code == 200
    assert empty.json()["turn_id"] == "turn-6"

    client.post(
        f"/api/projects/{project_id}/design/plan",
        json={
            "task_class": "A",
            "summary": "open-box",
            "strategy": "template_apply",
            "template_id": "open-box",
        },
    )
    state = client.get(f"/api/projects/{project_id}/design/state").json()
    assert state["plan"]["template_id"] == "open-box"


def test_design_review_retry_blocked_after_max(client, project_id):
    design_turn.begin_turn(project_id, "msg-7", turn_id="turn-7")
    design_turn._patch_turn(
        project_id,
        design_phase="review",
        render_phase="done",
        job_ids=["j1"],
        revision=8,
    )

    res = client.post(
        f"/api/projects/{project_id}/design/review",
        json={
            "turn_id": "turn-7",
            "status": "retry",
            "retry_phase": "plan",
            "notes": ["仍不满意"],
        },
    )
    assert res.status_code == 400
    assert "最大设计迭代" in res.json()["detail"]

    messages = storage.list_messages(project_id)
    assert any("设计迭代上限" in m.get("content", "") for m in messages)


def test_design_review_last_retry_warns(client, project_id):
    design_turn.begin_turn(project_id, "msg-8", turn_id="turn-8")
    design_turn._patch_turn(
        project_id,
        design_phase="review",
        render_phase="done",
        job_ids=["j1"],
        revision=7,
    )

    res = client.post(
        f"/api/projects/{project_id}/design/review",
        json={
            "turn_id": "turn-8",
            "status": "retry",
            "retry_phase": "author",
            "notes": ["Forge 执行有误"],
        },
    )
    assert res.status_code == 200
    assert res.json()["revision"] == 8

    messages = storage.list_messages(project_id)
    assert any("最后一次自动迭代" in m.get("content", "") for m in messages)


def test_auto_pass_review_when_agent_replied(client, project_id):
    design_turn.begin_turn(project_id, "msg-9", turn_id="turn-9")
    design_turn.ensure_implicit_plan(project_id, "turn-9", "测试立方体")
    design_turn.register_job(project_id, "turn-9", "job-9", prompt="测试立方体")
    design_turn.set_agent_replied(project_id, "turn-9", "asst-9")

    design_turn.sync_render_from_job(
        project_id,
        {
            "turn_id": "turn-9",
            "status": "succeeded",
            "version": 1,
        },
    )

    assert design_turn.get_active_turn(project_id) is None
    turn_meta = client.get(f"/api/projects/{project_id}/design/state").json()
    assert turn_meta is None


def test_turn_out_heals_stale_render_phase(project_id):
    from app.services import job_store

    design_turn.begin_turn(project_id, "msg-10", turn_id="turn-10")
    design_turn.register_job(project_id, "turn-10", "job-10", prompt="测试")
    job_store.save_job(
        {
            "id": "job-10",
            "project_id": project_id,
            "turn_id": "turn-10",
            "status": "succeeded",
            "version": 1,
            "kind": "render",
            "prompt": "测试",
            "created_at": "2026-01-01T00:00:00+00:00",
            "updated_at": "2026-01-01T00:00:01+00:00",
        }
    )

    turn = design_turn.turn_out(project_id, active_job=None)
    assert turn is not None
    assert turn.render_phase == "done"
    assert turn.version == 1


def test_turn_out_heals_stale_agent_phase(project_id):
    design_turn.begin_turn(project_id, "msg-11", turn_id="turn-11")
    design_turn.register_job(project_id, "turn-11", "job-11", prompt="测试")
    design_turn._patch_turn(
        project_id,
        agent_phase="running",
        assistant_message_id="asst-11",
    )

    turn = design_turn.turn_out(project_id, active_job=None)
    assert turn is not None
    assert turn.agent_phase == "replied"
    assert turn.render_phase == "running"
