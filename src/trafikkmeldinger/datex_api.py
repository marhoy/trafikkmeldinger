"""Twitter API Client."""

import os
from typing import cast

import requests
import requests_cache
from pydantic import HttpUrl, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from requests.auth import HTTPBasicAuth

namespaces = {
    "ns1": "http://datex2.eu/schema/3/common",
    "ns12": "http://datex2.eu/schema/3/situation",
    "ns8": "http://datex2.eu/schema/3/locationReferencing",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
}


class ApiConfig(BaseSettings):
    """Define configuration parameters."""

    model_config = SettingsConfigDict(
        env_file=os.getenv("TWITTER_CONFIG_ENV", "config.env")
    )

    DATEX_USERNAME: str = ""
    DATEX_PASSWORD: SecretStr = cast(SecretStr, "")
    USER_AGENT: str = "Python"
    BASE_URL: HttpUrl = cast(
        HttpUrl, "https://datex-server-get-v3-1.atlas.vegvesen.no/"
    )
    CACHE_NAME: str = "datex_cache"


class DatexSession(requests_cache.CachedSession):
    """A requests session towards the Twitter API."""

    def __init__(self, *args, **kwargs) -> None:  # type: ignore
        """Initialize class object."""
        config = ApiConfig()
        kwargs["cache_name"] = config.CACHE_NAME
        kwargs["expire_after"] = 1
        super().__init__(*args, **kwargs)
        self.auth = HTTPBasicAuth(
            config.DATEX_USERNAME, config.DATEX_PASSWORD.get_secret_value()
        )
        self.base_url = config.BASE_URL

    def request(  # type: ignore
        self, method: str, url: str, *args, **kwargs
    ) -> requests.models.Response:
        """Join the base URL and the endpoint."""
        url = f'{str(self.base_url).removesuffix("/")}/{url.removeprefix("/")}'
        response = super().request(method, url, *args, **kwargs)
        response.raise_for_status()
        return response


def get_situation_data(type: str | None) -> str:
    """Get situation."""
    session = DatexSession()
    path = "datexapi/GetSituation"  # /pullsnapshotdata/"
    if type:
        path += f"filter/{type}"
    response = session.get(path)
    return response.text
