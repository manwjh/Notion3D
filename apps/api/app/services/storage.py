import json
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.config import settings
from app.models.schemas import MessageRole, ProjectOut
from app.services.atomic_io import atomic_write_text
from app.services.links import project_web_url


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _project_dir(project_id: str) -> Path:
    return settings.data_dir / "projects" / project_id


def _meta_path(project_id: str) -> Path:
    return _project_dir(project_id) / "meta.json"


def _messages_path(project_id: str) -> Path:
    return _project_dir(project_id) / "messages.json"


def _project_from_meta(meta: dict) -> ProjectOut:
    return ProjectOut(
        id=meta["id"],
        name=meta["name"],
        created_at=datetime.fromisoformat(meta["created_at"]),
        updated_at=datetime.fromisoformat(meta["updated_at"]),
        latest_version=meta.get("latest_version"),
        web_url=project_web_url(meta["id"]),
    )


def create_project(name: str) -> ProjectOut:
    project_id = str(uuid.uuid4())
    root = _project_dir(project_id)
    (root / "versions").mkdir(parents=True, exist_ok=True)

    now = _utcnow()
    meta = {
        "id": project_id,
        "name": name,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
        "latest_version": None,
    }
    atomic_write_text(_meta_path(project_id), json.dumps(meta, ensure_ascii=False, indent=2))
    atomic_write_text(_messages_path(project_id), "[]")

    return _project_from_meta(meta)


def list_projects() -> list[ProjectOut]:
    root = settings.data_dir / "projects"
    if not root.exists():
        return []

    projects: list[ProjectOut] = []
    for path in sorted(root.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
        if not path.is_dir():
            continue
        meta_file = path / "meta.json"
        if not meta_file.exists():
            continue
        meta = json.loads(meta_file.read_text())
        projects.append(_project_from_meta(meta))
    return projects


def load_meta(project_id: str) -> dict:
    meta_file = _meta_path(project_id)
    if not meta_file.exists():
        raise ValueError("project not found")
    return json.loads(meta_file.read_text())


def get_project(project_id: str) -> ProjectOut | None:
    meta_file = _meta_path(project_id)
    if not meta_file.exists():
        return None
    meta = json.loads(meta_file.read_text())
    return _project_from_meta(meta)


def update_project_meta(project_id: str, **kwargs) -> None:
    meta_file = _meta_path(project_id)
    meta = json.loads(meta_file.read_text())
    meta.update(kwargs)
    meta["updated_at"] = _utcnow().isoformat()
    atomic_write_text(meta_file, json.dumps(meta, ensure_ascii=False, indent=2))
    _notify_project_state(project_id)


def next_version(project_id: str) -> int:
    project = get_project(project_id)
    if project is None:
        raise ValueError("project not found")
    version = (project.latest_version or 0) + 1
    update_project_meta(project_id, latest_version=version)
    return version


def version_dir(project_id: str, version: int) -> Path:
    path = _project_dir(project_id) / "versions" / str(version)
    path.mkdir(parents=True, exist_ok=True)
    return path


def project_attachments_dir(project_id: str, message_id: str) -> Path:
    path = _project_dir(project_id) / "attachments" / message_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def attachment_file_path(project_id: str, message_id: str, filename: str) -> Path | None:
    if ".." in filename.replace("\\", "/") or "/" in filename.replace("\\", "/"):
        return None
    target = project_attachments_dir(project_id, message_id) / filename
    return target if target.is_file() else None


def append_message(
    project_id: str,
    role: MessageRole,
    content: str,
    *,
    turn_id: str | None = None,
    job_id: str | None = None,
    message_id: str | None = None,
    images: list[dict] | None = None,
) -> dict:
    messages_file = _messages_path(project_id)
    messages = json.loads(messages_file.read_text()) if messages_file.exists() else []
    msg = {
        "id": message_id or str(uuid.uuid4()),
        "role": role.value,
        "content": content,
        "created_at": _utcnow().isoformat(),
        "turn_id": turn_id,
        "job_id": job_id,
    }
    if images:
        msg["images"] = images
    messages.append(msg)
    atomic_write_text(messages_file, json.dumps(messages, ensure_ascii=False, indent=2))
    _notify_project_state(project_id)
    return msg


def _notify_project_state(project_id: str) -> None:
    from app.services import project_events

    project_events.notify(project_id)


def list_messages(project_id: str) -> list[dict]:
    messages_file = _messages_path(project_id)
    if not messages_file.exists():
        return []
    return json.loads(messages_file.read_text())


def delete_project(project_id: str) -> bool:
    root = _project_dir(project_id)
    if not root.exists():
        return False
    shutil.rmtree(root)
    return True
