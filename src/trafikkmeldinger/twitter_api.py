"""Twitter API Client."""

import os
from typing import cast

import requests.auth
import requests_cache
from pydantic import HttpUrl, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

CONFIG_FILE = os.environ.get("CONFIG_FILE", "config.env")


class ApiConfig(BaseSettings):
    """Define configuration parameters."""

    # BaseSettings configuration.
    model_config = SettingsConfigDict(env_file=CONFIG_FILE, extra="ignore")

    BEARER_TOKEN: SecretStr
    USER_AGENT: str = "Python"
    BASE_URL: HttpUrl = cast(HttpUrl, "https://api.twitter.com/2/")


class TwitterAuth(requests.auth.AuthBase):
    """Authentication handling."""

    def __init__(self, config: ApiConfig) -> None:
        """Initialize class object."""
        self.token = config.BEARER_TOKEN
        self.user_agent = config.USER_AGENT

    def __call__(
        self, request: requests.models.PreparedRequest
    ) -> requests.models.PreparedRequest:
        """Add authentication headers to the request."""
        request.headers["Authorization"] = f"Bearer {self.token.get_secret_value()}"
        request.headers["User-Agent"] = self.user_agent
        return request


class TwitterSession(requests_cache.CachedSession):
    """A requests session towards the Twitter API."""

    def __init__(self, *args, **kwargs) -> None:  # type: ignore
        """Initialize class object."""
        super().__init__(*args, **kwargs)
        config = ApiConfig()
        self.auth = TwitterAuth(config=config)
        self.base_url = config.BASE_URL

    def request(  # type: ignore
        self, method: str, url: str, *args, **kwargs
    ) -> requests.models.Response:
        """Join the base URL and the endpoint."""
        url = f'{str(self.base_url).removesuffix("/")}/{url.removeprefix("/")}'
        response = super().request(method, url, *args, **kwargs)
        response.raise_for_status()
        return response
