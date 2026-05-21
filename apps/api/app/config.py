from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_REPO_ROOT = Path(__file__).resolve().parents[3]
_API_ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(
            str(_REPO_ROOT / ".env"),
            str(_API_ROOT / ".env"),
        ),
        env_prefix="NOTION3D_",
        extra="ignore",
        populate_by_name=True,
    )

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    data_dir: Path = _REPO_ROOT / "data"
    openscad_bin: str = "openscad"
    web_base_url: str = Field(
        default="http://localhost:5173",
        validation_alias=AliasChoices("NOTION3D_WEB_BASE", "NOTION3D_WEB_BASE_URL"),
    )

    # Web 对话 Agent：auto | cursor_sdk | openclaw | cursor_cloud
    agent_provider: str = "auto"
    notion3d_mcp_command: str = "notion3d-mcp"
    openclaw_bin: str = "openclaw"

    # Cursor SDK local bridge（@cursor/sdk，非 IDE，无需 tunnel）
    cursor_sdk_bridge_base: str = "http://127.0.0.1:8787"
    repo_root: Path = _REPO_ROOT

    # Cursor Cloud Agents API（非 Cursor IDE，需公网 tunnel）
    cursor_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("CURSOR_API_KEY", "NOTION3D_CURSOR_API_KEY"),
    )
    cursor_api_base: str = "https://api.cursor.com"
    cursor_model: str = "composer-2"
    public_api_base: str = ""  # Cloud Agent MCP 需能访问的 Notion3D API 地址

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
settings.data_dir.mkdir(parents=True, exist_ok=True)
