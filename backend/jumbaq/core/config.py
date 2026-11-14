from typing import Annotated, Literal, Self

from pydantic import SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Settings come from environment variables with the JUMBAQ_ prefix.

    The connection urls have no defaults: if one is missing, Settings() raises and the API or
    the worker does not start.
    """

    model_config = SettingsConfigDict(env_prefix="JUMBAQ_", extra="ignore")

    environment: Literal["dev", "test", "prod"] = "dev"
    log_level: str = "INFO"

    database_url: str
    redis_url: str

    # Browsers send a Secure cookie only over HTTPS, and Chrome and Firefox also to
    # http://localhost. Safari does not, so switch it off only to test in Safari locally.
    family_cookie_secure: bool = True
    family_cookie_days: int = 365

    # "stub" writes fixed stories without a network call. Tests and laptops without a key use it.
    ai_provider: Literal["stub", "claude"] = "stub"
    ai_api_key: SecretStr | None = None
    ai_model: str = "claude-opus-5-5"
    ai_timeout_seconds: float = 60
    # Every call costs money, so one family cannot start an endless chain of them.
    ai_daily_calls_per_family: int = 40

    @model_validator(mode="after")
    def check_ai_key(self) -> Self:
        # An empty JUMBAQ_AI_API_KEY= in a .env file counts as missing.
        has_key = self.ai_api_key is not None and self.ai_api_key.get_secret_value() != ""
        if self.ai_provider != "stub" and not has_key:
            raise ValueError("JUMBAQ_AI_API_KEY is needed for a real model")
        return self


class CorsSettings(BaseSettings):
    """The web app origins that may call the API from another host, with cookies.

    Separate from Settings, because create_app adds the middleware before the lifespan
    reads Settings, and this class needs no other variable.
    """

    model_config = SettingsConfigDict(env_prefix="JUMBAQ_", extra="ignore")

    # Comma separated, for example "https://jumbaq.kz". Empty: no CORS at all.
    cors_origins: Annotated[list[str], NoDecode] = []

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("cors_origins")
    @classmethod
    def check(cls, origins: list[str]) -> list[str]:
        # With cookies the browser does not accept "*" anyway.
        for origin in origins:
            scheme_ok = origin.startswith(("https://", "http://"))
            if not scheme_ok or "/" in origin.split("://", 1)[1] or "*" in origin:
                raise ValueError(f"not an origin: {origin}")
        return origins
