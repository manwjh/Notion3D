import json
from pathlib import Path

from app.config import settings

ACTIVE_STATUSES = frozenset({"pending", "running"})


def _jobs_dir() -> Path:
    return settings.data_dir / "jobs"


def save_job(job: dict) -> None:
    directory = _jobs_dir()
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{job['id']}.json"
    path.write_text(json.dumps(job, ensure_ascii=False, indent=2), encoding="utf-8")


def load_job(job_id: str) -> dict | None:
    path = _jobs_dir() / f"{job_id}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def list_all_jobs() -> list[dict]:
    directory = _jobs_dir()
    if not directory.exists():
        return []
    jobs: list[dict] = []
    for path in directory.glob("*.json"):
        try:
            jobs.append(json.loads(path.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            continue
    jobs.sort(key=lambda item: item.get("updated_at", ""), reverse=True)
    return jobs


def list_project_jobs(project_id: str) -> list[dict]:
    return [job for job in list_all_jobs() if job.get("project_id") == project_id]


def list_active_jobs(project_id: str | None = None) -> list[dict]:
    jobs = list_all_jobs()
    if project_id:
        jobs = [job for job in jobs if job.get("project_id") == project_id]
    return [job for job in jobs if job.get("status") in ACTIVE_STATUSES]


def find_job_for_version(project_id: str, version: int) -> dict | None:
    for job in list_project_jobs(project_id):
        if job.get("version") == version:
            return job
    return None


def find_active_job_for_version(project_id: str, version: int) -> dict | None:
    job = find_job_for_version(project_id, version)
    if job and job.get("status") in ACTIVE_STATUSES:
        return job
    return None


def message_exists_for_job(project_id: str, job_id: str) -> bool:
    from app.services import storage

    return any(item.get("job_id") == job_id for item in storage.list_messages(project_id))
