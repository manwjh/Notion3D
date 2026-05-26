"""Chat message image attachments."""

from __future__ import annotations

import base64
import binascii
import re
from app.services import storage
from app.services.cad_types import CadError

MAX_TURN_IMAGES = 3
MAX_IMAGE_BYTES = 2 * 1024 * 1024
ALLOWED_MIME = frozenset({"image/png", "image/jpeg", "image/webp", "image/gif"})
MIME_EXT = {
    "image/png": "png",
    "image/jpeg": "jpg",
    "image/webp": "webp",
    "image/gif": "gif",
}


def _decode_image_data(data: str) -> tuple[bytes, str]:
    raw = data.strip()
    mime_type = "image/png"
    if raw.startswith("data:"):
        match = re.match(r"^data:([^;]+);base64,(.+)$", raw, re.DOTALL | re.IGNORECASE)
        if not match:
            raise CadError("图片 data URL 格式无效")
        mime_type = match.group(1).lower()
        payload = match.group(2)
    else:
        payload = raw

    if mime_type not in ALLOWED_MIME:
        raise CadError(f"不支持的图片类型：{mime_type}")

    try:
        decoded = base64.b64decode(payload, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise CadError("图片 base64 解码失败") from exc

    if not decoded:
        raise CadError("图片内容为空")
    if len(decoded) > MAX_IMAGE_BYTES:
        raise CadError(f"单张图片不能超过 {MAX_IMAGE_BYTES // (1024 * 1024)}MB")

    return decoded, mime_type


def save_turn_images(
    project_id: str,
    message_id: str,
    images: list[dict],
) -> list[dict]:
    if len(images) > MAX_TURN_IMAGES:
        raise CadError(f"每条消息最多 {MAX_TURN_IMAGES} 张图片")

    out_dir = storage.project_attachments_dir(project_id, message_id)
    out_dir.mkdir(parents=True, exist_ok=True)

    saved: list[dict] = []
    for index, image in enumerate(images):
        decoded, mime_type = _decode_image_data(str(image.get("data") or ""))
        ext = MIME_EXT.get(mime_type, "png")
        filename = str(image.get("filename") or f"image-{index + 1}.{ext}")
        if not filename.lower().endswith(f".{ext}"):
            from pathlib import Path as _Path

            filename = f"{_Path(filename).stem}.{ext}"
        target = out_dir / filename
        target.write_bytes(decoded)
        saved.append(
            {
                "id": str(index),
                "filename": filename,
                "mime_type": mime_type,
                "url": f"/api/projects/{project_id}/messages/{message_id}/attachments/{filename}",
            }
        )
    return saved
