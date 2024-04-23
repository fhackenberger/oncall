import time
import typing

import requests

from lib.network import api_call as _api_call


class SplunkUser(typing.TypedDict):
    firstName: str
    lastName: str
    displayName: str
    username: str
    email: str
    createdAt: str



class SplunkUserPagingPolicy(typing.TypedDict):
    order: int
    timeout: int
    contactType: str
    extId: str


class SplunkOnCallAPIClient:
    """
    https://portal.victorops.com/public/api-docs.html
    """

    API_BASE_URL = "https://api.victorops.com/api-public/"

    def __init__(self, api_id: str, api_key: str):
        self.api_id = api_id
        self.api_key = api_key

    def _api_call(self, method: str, path: str, response_key: str, **kwargs) -> requests.Response:
        """
        According to the docs, most API endpoints may only be called a maximum of 2 times per second
        (hence the built-in `time.sleep`)
        """
        time.sleep(0.5)

        response = _api_call(method, self.API_BASE_URL, path,
            headers={
                "X-VO-Api-Id": self.api_id,
                "X-VO-Api-Key": self.api_key,
            },
            **kwargs,
        )

        return response.json()[response_key]

    def fetch_user_paging_policy(self, user_id: str) -> typing.List[SplunkUser]:
        """
        https://portal.victorops.com/public/api-docs.html#!/User32Paging32Policies/get_api_public_v1_user_user_policies
        """
        return self._api_call("GET", f"v2/user/{user_id}/policies", "policies")

    def fetch_users(self) -> typing.List[SplunkUser]:
        """
        https://portal.victorops.com/public/api-docs.html#!/Users/get_api_public_v2_user
        """
        users = self._api_call("GET", "v2/user", "users")
        # for user in users:
        return users
