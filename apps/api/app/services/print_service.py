import shutil
import subprocess
import urllib.parse
from pathlib import Path

from app.config import settings


class PrintError(Exception):
    pass


def bambu_connect_available() -> bool:
    if not settings.enable_bambu_connect:
        return False
    return shutil.which("open") is not None


def send_to_bambu_connect(file_path: Path, display_name: str) -> str:
    if not file_path.exists():
        raise PrintError(f"文件不存在: {file_path}")

    abs_path = file_path.resolve()
    url = (
        "bambu-connect://import-file?"
        f"path={urllib.parse.quote(str(abs_path), safe='')}"
        f"&name={urllib.parse.quote(display_name, safe='')}"
        "&version=1.0.0"
    )

    try:
        subprocess.run(["open", url], check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        raise PrintError(
            "无法唤起 Bambu Connect。请确认已安装并登录 Bambu Connect。"
        ) from exc
    except FileNotFoundError as exc:
        raise PrintError("当前系统不支持 open 命令") from exc

    return url
