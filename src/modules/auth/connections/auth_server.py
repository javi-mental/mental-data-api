import httpx

from src.config import ENVIRONMENT_CONFIG
from ..schemas import auth_schema


class AuthServer:
    def __init__(self, client: httpx.AsyncClient, loginEndpoint: str, refreshEndpoint: str):
        self._client = client
        self._loginEndpoint = loginEndpoint
        self._refreshEndpoint = refreshEndpoint

    async def login(self, email: str, password: str) -> auth_schema.UpstreamTokenPairSchema:
        requestBody = {
            "email": email,
            "password": password,
        }

        response = await self._client.post(self._loginEndpoint, json=requestBody)
        response.raise_for_status()

        return auth_schema.UpstreamTokenPairSchema.model_validate(response.json())

    async def refresh(self, refreshToken: str) -> auth_schema.UpstreamTokenPairSchema:
        headers = {
            "Authorization": f"Bearer {refreshToken}",
        }

        response = await self._client.post(self._refreshEndpoint, headers=headers)
        response.raise_for_status()

        return auth_schema.UpstreamTokenPairSchema.model_validate(response.json())

    async def close(self) -> None:
        await self._client.aclose()


config = ENVIRONMENT_CONFIG.AUTH_CONFIG

AUTH_SERVER_CONNECTION = AuthServer(
    client=httpx.AsyncClient(
        base_url=config.AUTH_BASE_URL,
        timeout=httpx.Timeout(timeout=config.AUTH_TIMEOUT_SECONDS),
        headers={"Connection": "close"},
    ),
    loginEndpoint=config.AUTH_LOGIN_ENDPOINT,
    refreshEndpoint=config.AUTH_REFRESH_ENDPOINT,
)