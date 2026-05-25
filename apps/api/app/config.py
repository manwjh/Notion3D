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
    templates_dir: Path = _REPO_ROOT / "templates"
    cad_backend: str = "forgecad"
    node_bin: str = "node"
    forgecad_bin: str = "forgecad"
    forge_runner_dir: Path = _REPO_ROOT / "apps" / "forge-runner"
    openscad_bin: str = "openscad"
    web_base_url: str = Field(
        default="http://localhost:5173",
        validation_alias=AliasChoices("NOTION3D_WEB_BASE", "NOTION3D_WEB_BASE_URL"),
    )

    # Web 对话 Agent：cursor_sdk | hermes | engine（engine = 禁用 Web 对话）
    agent_provider: str = "cursor_sdk"
    notion3d_mcp_command: str = "notion3d-mcp"

    # Cursor SDK local bridge（@cursor/sdk，非 Cursor IDE）
    cursor_sdk_bridge_base: str = "http://127.0.0.1:8787"
    repo_root: Path = _REPO_ROOT

    cursor_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("CURSOR_API_KEY", "NOTION3D_CURSOR_API_KEY"),
    )

    # Hermes Agent gateway API server（hermes gateway，默认 :8642）
    hermes_bin: str = "hermes"
    hermes_api_base: str = "http://127.0.0.1:8642"
    hermes_api_key: str = Field(
        default="",
        validation_alias=AliasChoices(
            "HERMES_API_SERVER_KEY",
            "NOTION3D_HERMES_API_KEY",
            "API_SERVER_KEY",
        ),
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def user_templates_dir(self) -> Path:
        return self.data_dir / "templates" / "user"


settings = Settings()
settings.data_dir.mkdir(parents=True, exist_ok=True)
settings.user_templates_dir.mkdir(parents=True, exist_ok=True)
