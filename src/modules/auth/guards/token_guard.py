import datetime
import logging

import fastapi
from fastapi import Request, status
from fastapi.responses import JSONResponse

from src.config import ENVIRONMENT_CONFIG
from ..repository import auth_repository
from ..utils import crypto_utils, token_utils

LOGGER = logging.getLogger("uvicorn").getChild("v1.auth.guards.token")


PUBLIC_PATH_PREFIXES = (
    "/auth/login",
    "/auth/refresh",
    "/v1/auth/login",
    "/v1/auth/refresh",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/health",
)


async def verifyAccessToken(request: Request) -> fastapi.Response | None:
    """Custom request check for FastAPI Guard that validates bearer tokens."""

    if _isPublicPath(request.url.path):
        return None

    authorization = request.headers.get("Authorization")
    if not authorization or not authorization.lower().startswith("bearer "):
        return _unauthorized("Falta el encabezado Authorization con Bearer token.")

    token = authorization[7:].strip()
    if not token:
        return _unauthorized("Token bearer vacío.")

    try:
        tokenData = token_utils.parseDerivedToken(token)
    except token_utils.TokenValidationError as error:
        LOGGER.warning("Token con formato inválido: %s", error)
        return _unauthorized("Token inválido.")

    session = await auth_repository.AUTH_SESSIONS_REPOSITORY.getSessionBySessionId(
        tokenData.sessionId
    )

    if session is None:
        LOGGER.warning("Sesión no encontrada para el token.")
        return _unauthorized("Sesión no encontrada o expirada.")

    accessExpiresAt = _ensureAware(session.accessExpiresAt)
    now = datetime.datetime.now(datetime.timezone.utc)

    if accessExpiresAt is not None:
        if accessExpiresAt <= now:
            LOGGER.info("Token expirado para la sesión %s", session.sessionId)
            return _unauthorized("El token ha expirado.")

    refreshExpiresAt = _ensureAware(session.refreshExpiresAt)

    expectedHash = token_utils.hashToken(token)
    if session.sessionTokenHash != expectedHash:
        LOGGER.warning("Hash del token no coincide para la sesión %s", session.sessionId)
        return _unauthorized("Token no válido.")

    try:
        upstreamAccessToken = crypto_utils.decryptUpstreamToken(session.upstreamAccessToken)
    except crypto_utils.TokenCipherError as error:
        LOGGER.error("No se pudo descifrar el token upstream para la sesión %s: %s", session.sessionId, error)
        return _unauthorized("Token inválido.")

    try:
        token_utils.verifyDerivedToken(
            token=token,
            upstreamToken=upstreamAccessToken,
            secret=ENVIRONMENT_CONFIG.AUTH_CONFIG.APP_AUTH_SECRET,
            expectedSessionId=session.sessionId,
        )
    except token_utils.TokenValidationError as error:
        LOGGER.warning("Firma inválida para la sesión %s: %s", session.sessionId, error)
        return _unauthorized("Token inválido.")

    if refreshExpiresAt is not None and refreshExpiresAt <= now:
        LOGGER.info("Refresh expirado para la sesión %s", session.sessionId)
        return _unauthorized("La sesión ha expirado.")

    request.state.authenticatedUser = session.user
    request.state.authSessionId = session.sessionId

    await auth_repository.AUTH_SESSIONS_REPOSITORY.updateSessionAccess(
        sessionId=session.sessionId,
        timestamp=now,
    )

    return None


def _isPublicPath(path: str) -> bool:
    return any(path.startswith(prefix) for prefix in PUBLIC_PATH_PREFIXES)


def _unauthorized(detail: str) -> fastapi.Response:
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": detail},
    )


def _ensureAware(dt: datetime.datetime | None) -> datetime.datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=datetime.timezone.utc)
    return dt


__all__ = ["verifyAccessToken"]