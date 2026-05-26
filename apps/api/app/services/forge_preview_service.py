"""ForgeCAD Studio preview sidecar for live parametric viewport."""

from __future__ import annotations

import asyncio
import logging
import shutil
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

from app.config import settings
from app.services import storage
from app.services.forgecad_service import forgecad_available

logger = logging.getLogger(__name__)

PREVIEW_PORT = 5174
_preview_proc: subprocess.Popen | None = None
_active_project_id: str | None = None


def _forgecad_cli() -> Path | None:
    cli = settings.forge_runner_dir / "node_modules" / "forgecad" / "dist-cli" / "forgecad.js"
    return cli if cli.exists() else None


def _studio_available() -> bool:
    dist = settings.forge_runner_dir / "node_modules" / "forgecad" / "dist" / "index.html"
    return dist.exists()


def _dev_runtime_available() -> bool:
    vite = (
        settings.forge_runner_dir
        / "node_modules"
        / "forgecad"
        / "node_modules"
        / "vite"
        / "bin"
        / "vite.js"
    )
    return vite.exists()


def preview_studio_available() -> bool:
    """True when ForgeCAD Studio can be served (dist build or dev runtime)."""
    if not forgecad_available():
        return False
    return _studio_available() or _dev_runtime_available()


def preview_workspace(project_id: str) -> Path:
    return settings.data_dir / "forge-preview" / project_id


def sync_preview_workspace(project_id: str, version: int) -> Path:
    ws = preview_workspace(project_id)
    src_root = storage.version_dir(project_id, version)
    forge_main = src_root / "model.forge.js"
    if not forge_main.exists():
        raise ValueError("该版本没有 Forge 源码")

    if ws.exists():
        shutil.rmtree(ws)
    ws.mkdir(parents=True)
    shutil.copy2(forge_main, ws / "model.forge.js")

    src_sub = src_root / "src"
    if src_sub.is_dir():
        shutil.copytree(src_sub, ws / "src")
    return ws


def _stop_preview() -> None:
    global _preview_proc, _active_project_id
    if _preview_proc and _preview_proc.poll() is None:
        _preview_proc.terminate()
        try:
            _preview_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            _preview_proc.kill()
    _preview_proc = None
    _active_project_id = None


async def _wait_http(port: int, timeout: float = 45) -> bool:
    url = f"http://127.0.0.1:{port}/"
    loop = asyncio.get_event_loop()
    deadline = loop.time() + timeout
    while loop.time() < deadline:
        try:
            await asyncio.to_thread(lambda: urllib.request.urlopen(url, timeout=1))
            return True
        except (urllib.error.URLError, TimeoutError, OSError):
            await asyncio.sleep(0.5)
    return False


def preview_public_url() -> str:
    return f"http://127.0.0.1:{PREVIEW_PORT}/"


def preview_embed_path() -> str:
    return "/forge-preview/"


async def ensure_preview(project_id: str, version: int) -> dict:
    if not forgecad_available():
        return {"ready": False, "url": None, "embed_url": None, "error": "ForgeCAD 未安装"}
    cli = _forgecad_cli()
    if not cli:
        return {"ready": False, "url": None, "embed_url": None, "error": "forgecad CLI 不可用"}

    try:
        sync_preview_workspace(project_id, version)
    except ValueError as exc:
        return {"ready": False, "url": None, "embed_url": None, "error": str(exc)}

    global _preview_proc, _active_project_id
    mode = "studio" if _studio_available() else "dev"
    need_restart = (
        _preview_proc is None
        or _preview_proc.poll() is not None
        or _active_project_id != project_id
    )

    if need_restart:
        _stop_preview()
        ws = preview_workspace(project_id)
        forge_root = settings.forge_runner_dir / "node_modules" / "forgecad"
        cmd = [
            settings.node_bin,
            str(cli),
            mode,
            str(ws),
            "--port",
            str(PREVIEW_PORT),
            "--host",
            "127.0.0.1",
        ]
        logger.info("Starting ForgeCAD %s preview for %s v%s", mode, project_id, version)
        _preview_proc = subprocess.Popen(
            cmd,
            cwd=str(forge_root),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        _active_project_id = project_id
        if not await _wait_http(PREVIEW_PORT):
            _stop_preview()
            return {
                "ready": False,
                "url": None,
                "embed_url": None,
                "error": "ForgeCAD Studio 启动超时",
            }

    return {
        "ready": True,
        "url": preview_public_url(),
        "embed_url": preview_embed_path(),
        "error": None,
        "mode": mode,
        "port": PREVIEW_PORT,
    }


def preview_running() -> bool:
    return _preview_proc is not None and _preview_proc.poll() is None
