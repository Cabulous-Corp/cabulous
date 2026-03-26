from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class DatabaseSettings(BaseModel):
    engine: str = "django.db.backends.postgresql"
    name: str = "cabulous"
    user: str = "cabulous"
    password: str = "cabulous"
    host: str = "db"
    port: int = 5432
    host_port: int = 5433


class RedisSettings(BaseModel):
    url: str = "redis://redis:6379/1"
    host_port: int = 6380


class CelerySettings(BaseModel):
    broker_url: str = "redis://redis:6379/0"
    result_backend: str = "redis://redis:6379/0"
    timezone: str = "America/Sao_Paulo"
    task_always_eager: bool = False
    beat_schedule_filename: str = "/tmp/celerybeat-schedule"


class MinioSettings(BaseModel):
    enabled: bool = True
    endpoint_url: str = "http://minio:9000"
    public_endpoint: str = "http://localhost:9000"
    access_key: str = "cabulous"
    secret_key: str = "cabulous123"
    bucket_name: str = "cabulous-media"
    region_name: str = "us-east-1"
    default_acl: str | None = None
    querystring_auth: bool = True


class JwtSettings(BaseModel):
    access_token_lifetime_minutes: int = 15
    refresh_token_lifetime_days: int = 7
    rotate_refresh_tokens: bool = True
    blacklist_after_rotation: bool = True
    update_last_login: bool = False
    auth_header_types: list[str] = Field(default_factory=lambda: ["Bearer"])
    flush_expired_tokens_hour: int = 3
    flush_expired_tokens_minute: int = 0


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )

    secret_key: str = "django-insecure-change-me-in-production"
    debug: bool = True
    allowed_hosts: list[str] = Field(default_factory=lambda: ["localhost", "127.0.0.1", "0.0.0.0"])
    time_zone: str = "America/Sao_Paulo"
    web_port: int = 8000
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    celery: CelerySettings = Field(default_factory=CelerySettings)
    minio: MinioSettings = Field(default_factory=MinioSettings)
    jwt: JwtSettings = Field(default_factory=JwtSettings)

    @field_validator("allowed_hosts", mode="before")
    @classmethod
    def split_allowed_hosts(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value


@lru_cache
def get_settings() -> AppSettings:
    return AppSettings()
