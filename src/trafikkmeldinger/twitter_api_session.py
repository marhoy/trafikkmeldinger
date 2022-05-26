"""Twitter API Client."""
import os

import requests
from pydantic import BaseSettings, Field, HttpUrl, SecretStr


class ApiConfig(BaseSettings):
    """Define configuration parameters."""

    BEARER_TOKEN: SecretStr
    USER_AGENT: str = "Python"
    BASE_URL: HttpUrl = Field("https://api.twitter.com/2/")

    class Config:
        """Get parameter values from file."""

        env_file = os.getenv("TWITTER_CONFIG_ENV", "config.env")


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


class TwitterSession(requests.Session):
    """A requests session towards the Twitter API."""

    def __init__(self, config_file: str = None) -> None:
        """Initialize class object."""
        super().__init__()
        if config_file is not None:
            config = ApiConfig(_env_file=config_file)  # type: ignore
        else:
            config = ApiConfig()
        self.auth = TwitterAuth(config=config)
        self.base_url = config.BASE_URL

    def request(  # type: ignore
        self, method: str, url: str, *args, **kwargs
    ) -> requests.models.Response:
        """Join the base URL and the endpoint."""
        url = f'{self.base_url.removesuffix("/")}/{url.removeprefix("/")}'
        response = super().request(method, url, *args, **kwargs)
        response.raise_for_status()
        return response
