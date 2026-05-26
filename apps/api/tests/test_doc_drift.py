"""Documentation drift checks — MCP tools, API paths, dependency docs."""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

SERVER_PY = REPO_ROOT / "apps/mcp-server/notion3d_mcp/server.py"
MCP_CLIENT_PY = REPO_ROOT / "apps/mcp-server/notion3d_mcp/client.py"
WEB_CLIENT_TS = REPO_ROOT / "apps/web/src/api/client.ts"
MCP_SKILL = REPO_ROOT / ".cursor/skills/notion3d-mcp/SKILL.md"
AGENTS_MD = REPO_ROOT / "AGENTS.md"
ARCHITECTURE_MD = REPO_ROOT / "docs/architecture.md"
README_MD = REPO_ROOT / "README.md"
DEPENDENCIES_MD = REPO_ROOT / "docs/dependencies.md"
USAGE_NETWORK_MD = REPO_ROOT / "docs/usage-network.md"
BRIDGE_MD = REPO_ROOT / "docs/agents/web-turn-bridge.md"
GATEWAY_MD = REPO_ROOT / "docs/agents/web-turn-gateway.md"
CAD_BACKEND_MD = REPO_ROOT / "docs/cad-backend-v2.md"

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
    assert len(tools) == 19, f"expected 19 MCP tools, found {len(tools)}: {sorted(tools)}"


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

# Web workbench client.ts — must stay aligned with Engine routes the UI calls.
WEB_CLIENT_ROUTE_TEMPLATES = (
    "/health",
    "/api/projects",
    "/api/projects/${projectId}/render-forge",
    "/api/projects/${projectId}/state",
    "/api/projects/${projectId}/state/events",
    "/api/projects/${projectId}/turn",
    "/api/projects/${projectId}/jobs/${jobId}",
    "/api/projects/${projectId}/jobs/${jobId}/events",
    "/api/projects/${projectId}/jobs/active",
    "/api/projects/${projectId}/versions/${version}/resume-stl",
    "/api/projects/${projectId}/versions",
)

MCP_CLIENT_ROUTE_TEMPLATES = (
    "/health",
    "/api/projects",
    "/api/projects/{project_id}/render-forge",
    "/api/projects/{project_id}/jobs/{job_id}",
    "/api/projects/{project_id}/jobs/{job_id}/events",
    "/api/projects/{project_id}/messages",
    "/api/projects/{project_id}/jobs/active",
    "/api/projects/{project_id}/versions",
    "/api/projects/{project_id}/versions/{version}/forge-sources",
    "/api/templates",
    "/api/templates/{template_id}",
    "/api/templates/{template_id}/apply",
    "/api/projects/{project_id}/versions/{version}/save-template",
    "/api/projects/{project_id}/design/plan",
    "/api/projects/{project_id}/design/review",
    "/api/projects/{project_id}/design/state",
    "/api/projects/{project_id}/state",
    "/api/projects/{project_id}/state/events",
)


def _web_client_text() -> str:
    assert WEB_CLIENT_TS.is_file(), f"missing web client: {WEB_CLIENT_TS}"
    return WEB_CLIENT_TS.read_text(encoding="utf-8")


def test_web_client_documents_required_routes():
    text = _web_client_text()
    missing = [route for route in WEB_CLIENT_ROUTE_TEMPLATES if route not in text]
    assert not missing, f"apps/web/src/api/client.ts missing routes: {missing}"


def test_mcp_client_documents_required_routes():
    assert MCP_CLIENT_PY.is_file(), f"missing MCP client: {MCP_CLIENT_PY}"
    text = MCP_CLIENT_PY.read_text(encoding="utf-8")
    missing = [route for route in MCP_CLIENT_ROUTE_TEMPLATES if route not in text]
    assert not missing, f"notion3d_mcp/client.py missing routes: {missing}"


def test_architecture_md_documents_key_api_paths():
    arch = ARCHITECTURE_MD.read_text(encoding="utf-8")
    missing = [path for path in KEY_API_PATHS if path not in arch]
    assert not missing, f"architecture.md missing API paths: {missing}"


def test_dependencies_doc_exists_and_covers_paths():
    assert DEPENDENCIES_MD.is_file(), "docs/dependencies.md missing"
    text = DEPENDENCIES_MD.read_text(encoding="utf-8")
    for phrase in (
        "Python",
        "3.11",
        "Node.js",
        "make install",
        "notion3d-mcp",
        "CURSOR_API_KEY",
        "forgecad",
        "LLM",
    ):
        assert phrase in text, f"dependencies.md missing: {phrase!r}"


def test_readme_links_dependencies_and_prerequisites():
    readme = README_MD.read_text(encoding="utf-8")
    assert "## 依赖与前置条件" in readme
    assert "docs/dependencies.md" in readme


def test_readme_documents_local_and_lan_usage():
    readme = README_MD.read_text(encoding="utf-8")
    assert "## 使用方式与网络" in readme
    assert "docs/usage-network.md" in readme
    assert "Local" in readme or "本机" in readme
    assert "局域网" in readme or "LAN" in readme


def test_usage_network_doc_covers_scenarios():
    assert USAGE_NETWORK_MD.is_file(), "docs/usage-network.md missing"
    text = USAGE_NETWORK_MD.read_text(encoding="utf-8")
    for phrase in ("本机", "局域网", "NOTION3D_WEB_BASE", "localhost"):
        assert phrase in text, f"usage-network.md missing: {phrase!r}"


def test_architecture_links_dependencies():
    arch = ARCHITECTURE_MD.read_text(encoding="utf-8")
    assert "dependencies.md" in arch


def test_bridge_doc_documents_sidecar_deps():
    text = BRIDGE_MD.read_text(encoding="utf-8")
    assert "## Sidecar 依赖" in text
    for phrase in ("notion3d-mcp", "CURSOR_API_KEY", "@cursor/sdk"):
        assert phrase in text, f"web-turn-bridge.md missing: {phrase!r}"


def test_gateway_doc_documents_sidecar_deps():
    text = GATEWAY_MD.read_text(encoding="utf-8")
    assert "## Sidecar 依赖" in text
    for phrase in ("gateway CLI", "notion3d-mcp", "LLM"):
        assert phrase in text, f"web-turn-gateway.md missing: {phrase!r}"


def test_cad_backend_documents_studio_from_npm():
    text = CAD_BACKEND_MD.read_text(encoding="utf-8")
    assert "npm" in text.lower()
    assert "5174" in text
    assert "forgecad_available" in text
