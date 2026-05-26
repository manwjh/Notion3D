"""Documentation drift checks — MCP tools and key API paths."""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

SERVER_PY = REPO_ROOT / "apps/mcp-server/notion3d_mcp/server.py"
MCP_SKILL = REPO_ROOT / ".cursor/skills/notion3d-mcp/SKILL.md"
AGENTS_MD = REPO_ROOT / "AGENTS.md"
ARCHITECTURE_MD = REPO_ROOT / "docs/architecture.md"

PRIMARY_MCP_TOOLS = frozenset(
    {
        "notion3d_health",
        "notion3d_report_design_plan",
        "notion3d_render_forge",
        "notion3d_wait_job",
        "notion3d_report_design_review",
        "notion3d_get_forge_sources",
        "notion3d_apply_template",
    }
)


def _mcp_tools_from_server() -> frozenset[str]:
    text = SERVER_PY.read_text(encoding="utf-8")
    return frozenset(re.findall(r"def (notion3d_\w+)\(", text))


def test_mcp_server_has_expected_tool_count():
    tools = _mcp_tools_from_server()
    assert len(tools) == 17, f"expected 17 MCP tools, found {len(tools)}: {sorted(tools)}"


def test_mcp_skill_documents_all_tools():
    skill = MCP_SKILL.read_text(encoding="utf-8")
    missing = [t for t in sorted(_mcp_tools_from_server()) if f"`{t}`" not in skill]
    assert not missing, f"notion3d-mcp SKILL missing tools: {missing}"


def test_agents_md_documents_primary_tools():
    agents = AGENTS_MD.read_text(encoding="utf-8")
    missing = [t for t in sorted(PRIMARY_MCP_TOOLS) if t not in agents]
    assert not missing, f"AGENTS.md missing primary tools: {missing}"


def test_architecture_md_documents_all_mcp_tools():
    arch = ARCHITECTURE_MD.read_text(encoding="utf-8")
    missing = [t for t in sorted(_mcp_tools_from_server()) if f"`{t}`" not in arch]
    assert not missing, f"architecture.md missing MCP tools: {missing}"


KEY_API_PATHS = (
    "/health",
    "/api/projects",
    "/api/projects/{id}/turn",
    "/api/projects/{id}/render-forge",
    "/api/projects/{id}/design/plan",
    "/api/projects/{id}/design/review",
    "/api/projects/{id}/versions/{v}/forge-preview",
    "/api/templates",
)


def test_architecture_md_documents_key_api_paths():
    arch = ARCHITECTURE_MD.read_text(encoding="utf-8")
    missing = [path for path in KEY_API_PATHS if path not in arch]
    assert not missing, f"architecture.md missing API paths: {missing}"
