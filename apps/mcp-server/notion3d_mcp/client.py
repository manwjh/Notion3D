"""HTTP client for Notion3D FastAPI."""

from __future__ import annotations

import json
import os
import time
from typing import Any

import httpx

API_BASE = os.environ.get("NOTION3D_API_BASE", "http://127.0.0.1:8000").rstrip("/")
DEFAULT_TIMEOUT = float(os.environ.get("NOTION3D_MCP_TIMEOUT", "30"))
JOB_POLL_INTERVAL = float(os.environ.get("NOTION3D_MCP_POLL_INTERVAL", "1.0"))
JOB_POLL_MAX = float(os.environ.get("NOTION3D_MCP_POLL_MAX", "600"))


class Notion3DClient:
    def __init__(self, base_url: str | None = None, timeout: float = DEFAULT_TIMEOUT) -> None:
        self.base_url = (base_url or API_BASE).rstrip("/")
        self.timeout = timeout

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def request(
        self,
        method: str,
        path: str,
        *,
        json_body: dict | None = None,
        timeout: float | None = None,
    ) -> Any:
        with httpx.Client(timeout=timeout or self.timeout) as client:
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

    def list_messages(self, project_id: str) -> list[dict]:
        return self.request("GET", f"/api/projects/{project_id}/messages")

    def template(
        self,
        project_id: str,
        prompt: str,
        pick: dict | None = None,
        region: str | None = None,
    ) -> dict:
        body: dict[str, Any] = {"prompt": prompt}
        if pick:
            body["pick"] = pick
        if region:
            body["region"] = region
        return self.request("POST", f"/api/projects/{project_id}/jobs/template", json_body=body)

    def render_scad(self, project_id: str, scad_code: str, label: str = "MCP 渲染 SCAD") -> dict:
        return self.request(
            "POST",
            f"/api/projects/{project_id}/render-scad",
            json_body={"scad_code": scad_code, "label": label},
        )

    def get_job(self, project_id: str, job_id: str) -> dict:
        return self.request("GET", f"/api/projects/{project_id}/jobs/{job_id}")

    def list_active_jobs(self, project_id: str) -> list[dict]:
        return self.request("GET", f"/api/projects/{project_id}/jobs/active")

    def list_versions(self, project_id: str) -> list[dict]:
        return self.request("GET", f"/api/projects/{project_id}/versions")

    def resume_stl(self, project_id: str, version: int) -> dict:
        return self.request("POST", f"/api/projects/{project_id}/versions/{version}/resume-stl")

    def wait_job(
        self,
        project_id: str,
        job_id: str,
        *,
        poll_interval: float = JOB_POLL_INTERVAL,
        max_wait: float = JOB_POLL_MAX,
    ) -> dict:
        deadline = time.monotonic() + max_wait
        while time.monotonic() < deadline:
            job = self.get_job(project_id, job_id)
            status = job.get("status")
            if status in ("succeeded", "failed"):
                return job
            time.sleep(poll_interval)
        raise TimeoutError(f"Job {job_id} did not finish within {max_wait}s")


def format_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)
