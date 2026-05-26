"""HTTP client for Notion3D FastAPI."""

from __future__ import annotations

import contextlib
import json
import os
import time
from typing import Any, Iterator

import httpx

API_BASE = os.environ.get("NOTION3D_API_BASE", "http://127.0.0.1:8000").rstrip("/")
DEFAULT_TIMEOUT = float(os.environ.get("NOTION3D_MCP_TIMEOUT", "30"))
JOB_POLL_INTERVAL = float(os.environ.get("NOTION3D_MCP_POLL_INTERVAL", "1.0"))
JOB_POLL_MAX = float(os.environ.get("NOTION3D_MCP_POLL_MAX", "600"))
TERMINAL_JOB_STATUSES = frozenset({"succeeded", "failed"})


class Notion3DClient:
    def __init__(
        self,
        base_url: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        *,
        http_client: httpx.Client | None = None,
    ) -> None:
        self.base_url = (base_url or API_BASE).rstrip("/")
        self.timeout = timeout
        self._external_client = http_client

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    @contextlib.contextmanager
    def _http(self, timeout: float | None = None) -> Iterator[httpx.Client]:
        if self._external_client is not None:
            yield self._external_client
            return
        with httpx.Client(timeout=timeout or self.timeout) as client:
            yield client

    def request(
        self,
        method: str,
        path: str,
        *,
        json_body: dict | None = None,
        timeout: float | None = None,
    ) -> Any:
        with self._http(timeout=timeout) as client:
            resp = client.request(method, self._url(path), json=json_body)
            if resp.status_code >= 400:
                detail = resp.text
                try:
                    detail = resp.json().get("detail", detail)
                except Exception:
                    pass
                raise RuntimeError(f"{method} {path} failed ({resp.status_code}): {detail}")
            if resp.status_code == 204:
                return None
            return resp.json()

    def health(self) -> dict:
        return self.request("GET", "/health")

    def list_projects(self) -> list[dict]:
        return self.request("GET", "/api/projects")

    def create_project(self, name: str = "Agent 项目") -> dict:
        return self.request("POST", "/api/projects", json_body={"name": name})

    def render_forge(
        self,
        project_id: str,
        forge_code: str,
        label: str = "MCP 渲染 ForgeCAD",
        *,
        source: str = "agent",
        files: dict[str, str] | None = None,
    ) -> dict:
        body: dict = {"forge_code": forge_code, "label": label, "source": source}
        if files:
            body["files"] = files
        return self.request(
            "POST",
            f"/api/projects/{project_id}/render-forge",
            json_body=body,
        )

    def get_job(self, project_id: str, job_id: str) -> dict:
        return self.request("GET", f"/api/projects/{project_id}/jobs/{job_id}")

    def list_messages(self, project_id: str) -> list[dict]:
        return self.request("GET", f"/api/projects/{project_id}/messages")

    def list_active_jobs(self, project_id: str) -> list[dict]:
        return self.request("GET", f"/api/projects/{project_id}/jobs/active")

    def list_versions(self, project_id: str) -> list[dict]:
        return self.request("GET", f"/api/projects/{project_id}/versions")

    def get_forge_sources(self, project_id: str, version: int) -> dict:
        return self.request(
            "GET",
            f"/api/projects/{project_id}/versions/{version}/forge-sources",
        )

    def _wait_job_sse(
        self,
        project_id: str,
        job_id: str,
        *,
        max_wait: float,
    ) -> dict | None:
        path = f"/api/projects/{project_id}/jobs/{job_id}/events"
        deadline = time.monotonic() + max_wait
        last: dict | None = None

        try:
            with self._http(timeout=max(max_wait, 30.0)) as client:
                with client.stream("GET", self._url(path)) as response:
                    if response.status_code >= 400:
                        return None
                    for line in response.iter_lines():
                        if time.monotonic() >= deadline:
                            break
                        if not line or not line.startswith("data: "):
                            continue
                        last = json.loads(line.removeprefix("data: "))
                        if last.get("status") in TERMINAL_JOB_STATUSES:
                            return last
        except Exception:
            if last and last.get("status") in TERMINAL_JOB_STATUSES:
                return last
            return None

        if last and last.get("status") in TERMINAL_JOB_STATUSES:
            return last
        return None

    def wait_job(
        self,
        project_id: str,
        job_id: str,
        *,
        poll_interval: float = JOB_POLL_INTERVAL,
        max_wait: float = JOB_POLL_MAX,
    ) -> dict:
        job = self.get_job(project_id, job_id)
        if job.get("status") in TERMINAL_JOB_STATUSES:
            return job

        streamed = self._wait_job_sse(project_id, job_id, max_wait=max_wait)
        if streamed is not None:
            return streamed

        deadline = time.monotonic() + max_wait
        current = job
        while time.monotonic() < deadline:
            if current.get("status") in TERMINAL_JOB_STATUSES:
                return current
            time.sleep(poll_interval)
            current = self.get_job(project_id, job_id)
        raise TimeoutError(f"Job {job_id} did not finish within {max_wait}s")

    def list_templates(
        self,
        *,
        tag: str | None = None,
        category: str | None = None,
        scope: str = "all",
    ) -> list[dict]:
        params: dict[str, str] = {"scope": scope}
        if tag:
            params["tag"] = tag
        if category:
            params["category"] = category
        query = "&".join(f"{k}={v}" for k, v in params.items())
        return self.request("GET", f"/api/templates?{query}")

    def get_template(self, template_id: str) -> dict:
        return self.request("GET", f"/api/templates/{template_id}")

    def apply_template(
        self,
        template_id: str,
        *,
        project_id: str | None = None,
        name: str | None = None,
        params: dict[str, float] | None = None,
        label: str | None = None,
    ) -> dict:
        body: dict[str, Any] = {}
        if project_id:
            body["project_id"] = project_id
        if name:
            body["name"] = name
        if params:
            body["params"] = params
        if label:
            body["label"] = label
        return self.request("POST", f"/api/templates/{template_id}/apply", json_body=body)

    def save_template(
        self,
        project_id: str,
        version: int,
        *,
        template_id: str,
        title: str,
        description: str | None = None,
        tags: list[str] | None = None,
        category: str | None = None,
    ) -> dict:
        body: dict[str, Any] = {"id": template_id, "title": title}
        if description:
            body["description"] = description
        if tags:
            body["tags"] = tags
        if category:
            body["category"] = category
        return self.request(
            "POST",
            f"/api/projects/{project_id}/versions/{version}/save-template",
            json_body=body,
        )

    def report_design_plan(
        self,
        project_id: str,
        *,
        task_class: str,
        summary: str,
        strategy: str,
        turn_id: str | None = None,
        template_id: str | None = None,
        params: dict[str, float] | None = None,
        modules: list[str] | None = None,
        assembly_spec: list[dict[str, object]] | None = None,
        geometry_recipes: list[dict[str, object]] | None = None,
        assumptions: list[str] | None = None,
        fidelity: str | None = None,
    ) -> dict:
        body: dict[str, Any] = {
            "task_class": task_class,
            "summary": summary,
            "strategy": strategy,
        }
        if turn_id:
            body["turn_id"] = turn_id
        if template_id:
            body["template_id"] = template_id
        if params:
            body["params"] = params
        if modules:
            body["modules"] = modules
        if assembly_spec:
            body["assembly_spec"] = assembly_spec
        if geometry_recipes:
            body["geometry_recipes"] = geometry_recipes
        if assumptions:
            body["assumptions"] = assumptions
        if fidelity:
            body["fidelity"] = fidelity
        return self.request("POST", f"/api/projects/{project_id}/design/plan", json_body=body)

    def report_design_review(
        self,
        project_id: str,
        *,
        status: str,
        turn_id: str | None = None,
        notes: list[str] | None = None,
        retry_phase: str | None = None,
    ) -> dict:
        body: dict[str, Any] = {"status": status}
        if turn_id:
            body["turn_id"] = turn_id
        if notes:
            body["notes"] = notes
        if retry_phase:
            body["retry_phase"] = retry_phase
        return self.request("POST", f"/api/projects/{project_id}/design/review", json_body=body)

    def get_design_state(self, project_id: str) -> dict | None:
        return self.request("GET", f"/api/projects/{project_id}/design/state")

    def get_project_state(self, project_id: str) -> dict:
        return self.request("GET", f"/api/projects/{project_id}/state")

    def _wait_project_state_sse(
        self,
        project_id: str,
        *,
        max_wait: float,
    ) -> dict | None:
        path = f"/api/projects/{project_id}/state/events"
        deadline = time.monotonic() + max_wait
        last: dict | None = None

        try:
            with self._http(timeout=max(max_wait, 30.0)) as client:
                with client.stream("GET", self._url(path)) as response:
                    if response.status_code >= 400:
                        return None
                    for line in response.iter_lines():
                        if time.monotonic() >= deadline:
                            break
                        if not line or not line.startswith("data: "):
                            continue
                        last = json.loads(line.removeprefix("data: "))
                        if not last.get("agent", {}).get("active"):
                            return last
        except Exception:
            if last and not last.get("agent", {}).get("active"):
                return last
            return None

        if last and not last.get("agent", {}).get("active"):
            return last
        return None

    def wait_agent(
        self,
        project_id: str,
        *,
        poll_interval: float = 2.0,
        max_wait: float = JOB_POLL_MAX,
    ) -> dict:
        state = self.get_project_state(project_id)
        if not state.get("agent", {}).get("active"):
            return state

        streamed = self._wait_project_state_sse(project_id, max_wait=max_wait)
        if streamed is not None:
            return streamed

        deadline = time.monotonic() + max_wait
        current = state
        while current.get("agent", {}).get("active") and time.monotonic() < deadline:
            time.sleep(poll_interval)
            current = self.get_project_state(project_id)
        return current


def format_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)
