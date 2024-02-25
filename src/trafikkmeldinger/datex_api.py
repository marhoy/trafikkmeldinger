"""Datex API Client."""

from urllib.parse import urljoin

import requests
import requests_cache
from requests.auth import HTTPBasicAuth

from trafikkmeldinger import config

# Can be created from the XML:
# namespaces = dict(
#    [node for _, node in ET.iterparse(StringIO(r.text), events=["start-ns"])]
# )

namespaces = {
    "": "http://datex2.eu/schema/3/common",
    "ns2": "http://datex2.eu/schema/3/messageContainer",
    "ns3": "http://datex2.eu/schema/3/cisInformation",
    "ns4": "http://datex2.eu/schema/3/exchangeInformation",
    "ns5": "http://datex2.eu/schema/3/informationManagement",
    "ns6": "http://datex2.eu/schema/3/locationReferencing",
    "ns7": "http://datex2.eu/schema/3/dataDictionaryExtension",
    "ns8": "http://datex2.eu/schema/3/cctvExtension",
    "ns9": "http://datex2.eu/schema/3/alertCLocationCodeTableExtension",
    "ns10": "http://datex2.eu/schema/3/roadTrafficData",
    "ns11": "http://datex2.eu/schema/3/vms",
    "ns12": "http://datex2.eu/schema/3/situation",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
}

BASE_URL = "https://datex-server-get-v3-1.atlas.vegvesen.no/"
CACHE_NAME: str = "datex_cache"


class DatexSession(requests_cache.CachedSession):
    """A requests session towards the Twitter API."""

    def __init__(self, *args, **kwargs) -> None:  # type: ignore
        """Initialize class object."""
        kwargs["cache_name"] = CACHE_NAME
        # The cache will still be used, until Last-Modified > If-Modified-Since
        kwargs["expire_after"] = 1  # In seconds
        super().__init__(*args, **kwargs)
        self.auth = HTTPBasicAuth(
            config.DATEX_USERNAME,
            config.DATEX_PASSWORD.get_secret_value(),
        )

    def request(  # type: ignore
        self, method: str, url: str, *args, **kwargs
    ) -> requests.models.Response:
        """Run specified request."""
        response = super().request(
            method,
            urljoin(BASE_URL, url),
            *args,
            **kwargs,
        )
        response.raise_for_status()
        return response


def get_situation_xml(type: str | None = None) -> str:
    """Get situation XML-data."""
    with DatexSession() as session:
        path = "datexapi/GetSituation/pullsnapshotdata"
        if type:
            path += f"/filter/{type}"
        response = session.get(path)
        return response.text
