from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="NOTION3D_", extra="ignore")

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    data_dir: Path = Path(__file__).resolve().parents[3] / "data"
    openscad_bin: str = "openscad"
    orca_slicer_bin: str | None = None
    enable_bambu_connect: bool = True
    web_base_url: str = "http://localhost:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
settings.data_dir.mkdir(parents=True, exist_ok=True)
