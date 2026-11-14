from typing import Annotated, Literal

from pydantic import field_validator
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
