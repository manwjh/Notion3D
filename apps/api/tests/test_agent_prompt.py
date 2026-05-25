"""Agent prompt content."""

from app.services.agents.prompt import build_agent_prompt


def test_prompt_includes_forge_render():
    text = build_agent_prompt("proj-1", "做一个电动牙刷装配", turn_id="turn-abc")
    assert 'project_id="proj-1"' in text
    assert "notion3d_render_forge" in text
    assert "forge.js" in text


def test_prompt_chat_only_path():
    text = build_agent_prompt("proj-1", "你好")
    assert "chat_only" in text
    assert "不要 render" in text


def test_prompt_demo_templates_not_required():
    text = build_agent_prompt("proj-1", "做一个盒子")
    assert "不要为每个请求先 list_templates" in text
    assert "from_scratch" in text


def test_prompt_modification_hints():
    text = build_agent_prompt("proj-1", "把盒子加高", latest_version=3)
    assert "v3" in text
    assert "notion3d_get_forge_sources" in text
