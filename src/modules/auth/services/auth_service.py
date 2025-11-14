import datetime
import logging
import uuid

import fastapi
import httpx
import pydantic

from src.config import ENVIRONMENT_CONFIG
from ..repository import auth_repository
from ..schemas import auth_schema
from ..connections.auth_server import AUTH_SERVER_CONNECTION
from ..utils import crypto_utils, token_utils

LOGGER = logging.getLogger("uvicorn").getChild("v1.auth.services.auth")


async def loginUser(payload: auth_schema.LoginRequestSchema) -> auth_schema.LoginResponseSchema:
    """Autentica contra el servidor upstream y genera tokens derivados."""

    if not ENVIRONMENT_CONFIG.AUTH_CONFIG.AUTH_BASE_URL:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AUTH_BASE_URL no está configurado."
        )

    if not ENVIRONMENT_CONFIG.AUTH_CONFIG.APP_AUTH_SECRET:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="APP_AUTH_SECRET no está configurado."
        )

    upstreamResponse = await _performUpstreamLogin(payload)
    userData = upstreamResponse.user or {}

    sessionId = uuid.uuid4().hex
    issuedAt = datetime.datetime.now(datetime.timezone.utc)

    # Calculamos los tiempos de expiración
    # Este es el tiempo del token de acceso derivado
    # Se calcula sumando el tiempo de emisión y la duración del token
    # Si este expira antes que el token upstream, el usuario tendrá que reautenticarse
    accessExpiresAt = _calculateExpiry(
        issuedAt,
        upstreamResponse.expiresIn,
        ENVIRONMENT_CONFIG.AUTH_CONFIG.DERIVED_TOKEN_TTL_SECONDS,
    )

    # Construimos los tokens derivados
    # este es el de acceso
    derivedAccessToken = token_utils.buildDerivedToken(
        sessionId=sessionId,
        upstreamToken=upstreamResponse.accessToken,
        issuedAt=issuedAt,
        secret=ENVIRONMENT_CONFIG.AUTH_CONFIG.APP_AUTH_SECRET,
    )

    # Aca decidimos el secreto para el refresh token
    # Si no hay un secreto específico para el refresh, usamos el del access
    # Por lo general, es buena práctica usar secretos diferentes para access y refresh tokens
    refreshSecret = ENVIRONMENT_CONFIG.AUTH_CONFIG.APP_REFRESH_SECRET or ENVIRONMENT_CONFIG.AUTH_CONFIG.APP_AUTH_SECRET

    # Calculamos el tiempo de expiración del refresh token
    # Usamos session TTL ya que si la sesion expira, el refresh también debe hacerlo
    # El refresh se usa para obtener nuevos tokens de acceso cuando estos expiran
    # Por lo general, el refresh token tiene una duración mayor que el token de acceso
    refreshExpiresAt = _calculateExpiry(
        issuedAt,
        upstreamResponse.refreshExpiresIn,
        ENVIRONMENT_CONFIG.AUTH_CONFIG.SESSION_TTL_SECONDS,
    )

    derivedRefreshToken = token_utils.buildDerivedToken(
        sessionId=sessionId,
        upstreamToken=upstreamResponse.refreshToken,
        issuedAt=issuedAt,
        secret=refreshSecret,
    )

    try:
        encryptedUpstreamAccessToken = crypto_utils.encryptUpstreamToken(
            upstreamResponse.accessToken
        )
        encryptedUpstreamRefreshToken = crypto_utils.encryptUpstreamToken(
            upstreamResponse.refreshToken
        )
    except crypto_utils.TokenCipherError as error:
        LOGGER.error("Error al cifrar los tokens upstream: %s", error)
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al proteger tokens de autenticación.",
        ) from error

    sessionDocument = auth_schema.AuthSessionSchema(
        sessionId=sessionId,
        sessionTokenHash=token_utils.hashToken(derivedAccessToken),
        refreshTokenHash=token_utils.hashToken(derivedRefreshToken),
        upstreamAccessToken=encryptedUpstreamAccessToken,
        upstreamRefreshToken=encryptedUpstreamRefreshToken,
        user=userData,
        issuedAt=issuedAt,
        lastAccessAt=issuedAt,
        accessExpiresAt=accessExpiresAt,
        refreshExpiresAt=refreshExpiresAt,
    )

    # Creamos la sesión en la base de datos
    # Así persistimos la sesión del usuario
    # Y también podemos invalidarla si es necesario
    await auth_repository.AUTH_SESSIONS_REPOSITORY.createSession(sessionDocument)

    # Limitamos a dos sesiones por usuario, conservando las más recientes.
    await auth_repository.AUTH_SESSIONS_REPOSITORY.trimSessionsForUser(
        user=sessionDocument.user,
        maxSessions=2,
    )

    return auth_schema.LoginResponseSchema(
        accessToken=derivedAccessToken,
        refreshToken=derivedRefreshToken,
        user=upstreamResponse.user,
    )


async def refreshSession(payload: auth_schema.RefreshRequestSchema) -> auth_schema.LoginResponseSchema:
    """Refresca los tokens derivados utilizando el refresh token del upstream."""

    if not ENVIRONMENT_CONFIG.AUTH_CONFIG.APP_AUTH_SECRET:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="APP_AUTH_SECRET no está configurado.",
        )

    try:
        tokenData = token_utils.parseDerivedToken(payload.refreshToken)
    except token_utils.TokenValidationError as error:
        LOGGER.info("Refresh token con formato inválido: %s", error)
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido.",
        ) from error

    session = await auth_repository.AUTH_SESSIONS_REPOSITORY.getSessionBySessionId(
        tokenData.sessionId
    )

    if session is None:
        LOGGER.info("Sesión no encontrada durante refresh para %s", tokenData.sessionId)
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_401_UNAUTHORIZED,
            detail="Sesión no encontrada o expirada.",
        )

    now = datetime.datetime.now(datetime.timezone.utc)

    if session.refreshExpiresAt is not None and session.refreshExpiresAt <= now:
        LOGGER.info("Refresh expirado para la sesión %s", session.sessionId)
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_401_UNAUTHORIZED,
            detail="La sesión ha expirado.",
        )

    expectedRefreshHash = token_utils.hashToken(payload.refreshToken)
    if session.refreshTokenHash != expectedRefreshHash:
        LOGGER.warning("Refresh token hash no coincide para la sesión %s", session.sessionId)
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido.",
        )

    refreshSecret = ENVIRONMENT_CONFIG.AUTH_CONFIG.APP_REFRESH_SECRET or ENVIRONMENT_CONFIG.AUTH_CONFIG.APP_AUTH_SECRET

    try:
        upstreamRefreshToken = crypto_utils.decryptUpstreamToken(session.upstreamRefreshToken)
    except crypto_utils.TokenCipherError as error:
        LOGGER.error("No se pudo descifrar el refresh token upstream para la sesión %s: %s", session.sessionId, error)
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al validar la sesión.",
        ) from error

    try:
        token_utils.verifyDerivedToken(
            token=payload.refreshToken,
            upstreamToken=upstreamRefreshToken,
            secret=refreshSecret,
            expectedSessionId=session.sessionId,
        )
    except token_utils.TokenValidationError as error:
        LOGGER.warning("Firma de refresh inválida para la sesión %s: %s", session.sessionId, error)
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido.",
        ) from error

    upstreamResponse = await _performUpstreamRefresh(upstreamRefreshToken)

    issuedAt = datetime.datetime.now(datetime.timezone.utc)

    accessExpiresAt = _calculateExpiry(
        issuedAt,
        upstreamResponse.expiresIn,
        ENVIRONMENT_CONFIG.AUTH_CONFIG.DERIVED_TOKEN_TTL_SECONDS,
    )

    derivedAccessToken = token_utils.buildDerivedToken(
        sessionId=session.sessionId,
        upstreamToken=upstreamResponse.accessToken,
        issuedAt=issuedAt,
        secret=ENVIRONMENT_CONFIG.AUTH_CONFIG.APP_AUTH_SECRET,
    )

    refreshExpiresAt = _calculateExpiry(
        issuedAt,
        upstreamResponse.refreshExpiresIn,
        ENVIRONMENT_CONFIG.AUTH_CONFIG.SESSION_TTL_SECONDS,
    )

    derivedRefreshToken = token_utils.buildDerivedToken(
        sessionId=session.sessionId,
        upstreamToken=upstreamResponse.refreshToken,
        issuedAt=issuedAt,
        secret=refreshSecret,
    )

    try:
        encryptedUpstreamAccessToken = crypto_utils.encryptUpstreamToken(
            upstreamResponse.accessToken
        )
        encryptedUpstreamRefreshToken = crypto_utils.encryptUpstreamToken(
            upstreamResponse.refreshToken
        )
    except crypto_utils.TokenCipherError as error:
        LOGGER.error("Error al cifrar nuevos tokens upstream para la sesión %s: %s", session.sessionId, error)
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al proteger tokens de autenticación.",
        ) from error

    await auth_repository.AUTH_SESSIONS_REPOSITORY.updateSessionTokens(
        sessionId=session.sessionId,
        sessionTokenHash=token_utils.hashToken(derivedAccessToken),
        refreshTokenHash=token_utils.hashToken(derivedRefreshToken),
        upstreamAccessToken=encryptedUpstreamAccessToken,
        upstreamRefreshToken=encryptedUpstreamRefreshToken,
        accessExpiresAt=accessExpiresAt,
        refreshExpiresAt=refreshExpiresAt,
        timestamp=issuedAt,
    )

    return auth_schema.LoginResponseSchema(
        accessToken=derivedAccessToken,
        refreshToken=derivedRefreshToken,
        user=session.user,
    )


async def _performUpstreamLogin(
    payload: auth_schema.LoginRequestSchema,
) -> auth_schema.UpstreamTokenPairSchema:
    try:
        response = await AUTH_SERVER_CONNECTION.login(
            email=payload.email,
            password=payload.password,
        )
        upstreamUserId = response.user.get("_id") if isinstance(response.user, dict) else None
        LOGGER.info(
            "Login exitoso contra el servidor upstream para %s (userId=%s)",
            payload.email,
            upstreamUserId,
        )
        return response
    except httpx.HTTPStatusError as error:
        statusCode = error.response.status_code
        if statusCode in {fastapi.status.HTTP_400_BAD_REQUEST, fastapi.status.HTTP_401_UNAUTHORIZED, fastapi.status.HTTP_403_FORBIDDEN}:
            LOGGER.warning("Login rechazado por el upstream. Código %s", statusCode)
            raise fastapi.HTTPException(
                status_code=fastapi.status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales inválidas o no autorizadas."
            ) from error

        LOGGER.error("Error de estado al comunicarse con el servidor de auth: %s", error)
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_502_BAD_GATEWAY,
            detail="Error al comunicarse con el servidor de autenticación."
        ) from error
    except httpx.RequestError as error:
        LOGGER.error("Error de red al comunicar con el servidor de auth: %s", error)
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_502_BAD_GATEWAY,
            detail="No se pudo contactar al servidor de autenticación."
        ) from error
    except pydantic.ValidationError as error:
        LOGGER.error("Respuesta del upstream no coincide con el esquema esperado: %s", error)
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_502_BAD_GATEWAY,
            detail="Respuesta inesperada del servidor de autenticación."
        ) from error


def _calculateExpiry(
    issuedAt: datetime.datetime,
    upstreamTtl: int | None,
    fallbackTtl: int | None,
) -> datetime.datetime | None:
    ttlSeconds = upstreamTtl or fallbackTtl
    if ttlSeconds is None:
        return None
    return issuedAt + datetime.timedelta(seconds=ttlSeconds)


async def _performUpstreamRefresh(
    refreshToken: str,
) -> auth_schema.UpstreamTokenPairSchema:
    try:
        return await AUTH_SERVER_CONNECTION.refresh(refreshToken)
    except httpx.HTTPStatusError as error:
        statusCode = error.response.status_code
        if statusCode in {
            fastapi.status.HTTP_400_BAD_REQUEST,
            fastapi.status.HTTP_401_UNAUTHORIZED,
            fastapi.status.HTTP_403_FORBIDDEN,
        }:
            LOGGER.warning("Refresh rechazado por el upstream. Código %s", statusCode)
            raise fastapi.HTTPException(
                status_code=fastapi.status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token inválido o expirado.",
            ) from error

        LOGGER.error("Error de estado al refrescar con el servidor de auth: %s", error)
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_502_BAD_GATEWAY,
            detail="Error al comunicarse con el servidor de autenticación.",
        ) from error
    except httpx.RequestError as error:
        LOGGER.error("Error de red al refrescar con el servidor de auth: %s", error)
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_502_BAD_GATEWAY,
            detail="No se pudo contactar al servidor de autenticación.",
        ) from error
    except pydantic.ValidationError as error:
        LOGGER.error("Respuesta de refresh del upstream inválida: %s", error)
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_502_BAD_GATEWAY,
            detail="Respuesta inesperada del servidor de autenticación.",
        ) from error

