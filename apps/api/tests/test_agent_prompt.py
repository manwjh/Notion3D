"""Agent prompt content."""

from app.services.agents.prompt import build_agent_prompt


def test_prompt_includes_forge_render():
    text = build_agent_prompt("proj-1", "做一个电动牙刷装配", turn_id="turn-abc")
    assert 'project_id="proj-1"' in text
    assert "notion3d_render_forge" in text
    assert "render-first" in text


def test_prompt_chat_only_path():
    text = build_agent_prompt("proj-1", "你好")
    assert "chat_only" in text
    assert "不 render" in text


def test_prompt_render_first_loop():
    text = build_agent_prompt("proj-1", "做一个盒子")
    assert "wait_job" in text
    assert "get_forge_sources" in text


def test_prompt_modification_hints():
    text = build_agent_prompt("proj-1", "把盒子加高", latest_version=3)
    assert "v3" in text
    assert "notion3d_get_forge_sources" in text
