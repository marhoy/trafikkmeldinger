"""Configuration parameters for the trafikkmeldinger package."""

import os
from typing import cast

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class TrafikkmeldingerConfig(BaseSettings):
    """Define configuration parameters."""

    model_config = SettingsConfigDict(env_file=os.getenv("CONFIG_ENV", "config.env"))

    DATEX_USERNAME: str = ""
    DATEX_PASSWORD: SecretStr = cast(SecretStr, "")
    USER_AGENT: str = "Python"


settings = TrafikkmeldingerConfig()
