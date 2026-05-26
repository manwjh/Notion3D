from pathlib import Path

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.services.web_turn_config import normalize_web_turn

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
    web_base_url: str = Field(
        default="http://localhost:5173",
        validation_alias=AliasChoices("NOTION3D_WEB_BASE", "NOTION3D_WEB_BASE_URL"),
    )

    # Web Turn sidecar: off | bridge | gateway（浏览器 POST /turn 可选接口）
    web_turn: str = Field(
        default="off",
        validation_alias=AliasChoices("NOTION3D_WEB_TURN", "NOTION3D_AGENT_PROVIDER"),
    )
    notion3d_mcp_command: str = "notion3d-mcp"

    web_turn_bridge_base: str = Field(
        default="http://127.0.0.1:8787",
        validation_alias=AliasChoices(
            "NOTION3D_WEB_TURN_BRIDGE_BASE",
            "NOTION3D_CURSOR_SDK_BRIDGE_BASE",
        ),
    )
    repo_root: Path = _REPO_ROOT

    web_turn_bridge_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("CURSOR_API_KEY", "NOTION3D_CURSOR_API_KEY"),
    )

    web_turn_gateway_bin: str = Field(
        default="hermes",
        validation_alias=AliasChoices("NOTION3D_WEB_TURN_GATEWAY_BIN", "NOTION3D_HERMES_BIN"),
    )
    web_turn_gateway_base: str = Field(
        default="http://127.0.0.1:8642",
        validation_alias=AliasChoices("NOTION3D_WEB_TURN_GATEWAY_BASE", "NOTION3D_HERMES_API_BASE"),
    )
    web_turn_gateway_api_key: str = Field(
        default="",
        validation_alias=AliasChoices(
            "HERMES_API_SERVER_KEY",
            "NOTION3D_HERMES_API_KEY",
            "NOTION3D_WEB_TURN_GATEWAY_API_KEY",
            "API_SERVER_KEY",
        ),
    )

    @field_validator("web_turn", mode="before")
    @classmethod
    def _normalize_web_turn(cls, value: object) -> str:
        return normalize_web_turn(str(value) if value is not None else None)

    @property
    def normalized_web_turn(self) -> str:
        return self.web_turn

    # Deprecated aliases — internal/backward compat only
    @property
    def agent_provider(self) -> str:
        return self.web_turn

    @property
    def cursor_sdk_bridge_base(self) -> str:
        return self.web_turn_bridge_base

    @property
    def cursor_api_key(self) -> str:
        return self.web_turn_bridge_api_key

    @property
    def hermes_bin(self) -> str:
        return self.web_turn_gateway_bin

    @property
    def hermes_api_base(self) -> str:
        return self.web_turn_gateway_base

    @property
    def hermes_api_key(self) -> str:
        return self.web_turn_gateway_api_key

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def user_templates_dir(self) -> Path:
        return self.data_dir / "templates" / "user"


settings = Settings()
settings.data_dir.mkdir(parents=True, exist_ok=True)
settings.user_templates_dir.mkdir(parents=True, exist_ok=True)
