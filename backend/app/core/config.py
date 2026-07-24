from __future__ import annotations

from functools import lru_cache

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(default="ReportFlow AI", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    debug: bool = Field(default=True, alias="DEBUG")
    api_v1_prefix: str = Field(default="/api/v1", alias="API_V1_PREFIX")

    mysql_database: str = Field(default="reportflow", alias="MYSQL_DATABASE")
    mysql_user: str = Field(default="reportflow", alias="MYSQL_USER")
    mysql_password: str = Field(default="change_me", alias="MYSQL_PASSWORD")
    mysql_root_password: str = Field(
        default="change_root_password",
        alias="MYSQL_ROOT_PASSWORD",
    )
    mysql_host: str = Field(default="mysql", alias="MYSQL_HOST")
    mysql_port: int = Field(default=3306, alias="MYSQL_PORT")
    database_url: str | None = Field(default=None, alias="DATABASE_URL")
    jwt_secret_key: str = Field(default="change-me-in-local-env", alias="JWT_SECRET_KEY")
    access_token_expire_minutes: int = Field(default=1440, alias="ACCESS_TOKEN_EXPIRE_MINUTES")

    storage_root: str = Field(default="./storage", alias="STORAGE_ROOT")
    ocr_provider: str = Field(default="mock", alias="OCR_PROVIDER")
    qwen_api_key: str | None = Field(default=None, alias="QWEN_API_KEY")
    qwen_base_url: str = Field(
        default="https://dashscope.aliyuncs.com/compatible-mode/v1",
        alias="QWEN_BASE_URL",
    )
    qwen_vision_model: str = Field(default="qwen3-vl-plus", alias="QWEN_VISION_MODEL")
    qwen_timeout_seconds: float = Field(default=60.0, alias="QWEN_TIMEOUT_SECONDS")
    github_api_token: str | None = Field(default=None, alias="GITHUB_API_TOKEN")
    github_api_base_url: str = Field(default="https://api.github.com", alias="GITHUB_API_BASE_URL")
    github_timeout_seconds: float = Field(default=30.0, alias="GITHUB_TIMEOUT_SECONDS")
    ai_provider: str = Field(default="mock", alias="AI_PROVIDER")
    ai_api_key: str | None = Field(default=None, alias="AI_API_KEY")
    ai_base_url: str | None = Field(default=None, alias="AI_BASE_URL")
    ai_model: str = Field(default="mock-reportflow", alias="AI_MODEL")
    ai_timeout_seconds: float = Field(default=60.0, alias="AI_TIMEOUT_SECONDS")
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://127.0.0.1:5173"],
        alias="CORS_ORIGINS",
    )

    model_config = SettingsConfigDict(
        env_file="../.env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug(cls, value: bool | str) -> bool:
        if isinstance(value, str):
            lowered = value.strip().lower()
            if lowered in {"1", "true", "yes", "on", "debug"}:
                return True
            if lowered in {"0", "false", "no", "off", "release", "prod", "production"}:
                return False
        return bool(value)

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @model_validator(mode="after")
    def build_database_url(self) -> Settings:
        if not self.database_url:
            self.database_url = (
                "mysql+pymysql://"
                f"{self.mysql_user}:{self.mysql_password}@"
                f"{self.mysql_host}:{self.mysql_port}/"
                f"{self.mysql_database}?charset=utf8mb4"
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
