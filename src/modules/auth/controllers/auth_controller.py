import fastapi
import logging
from fastapi import Request, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from ..schemas import auth_schema
from ..services import auth_service, session_service

LOGGER = logging.getLogger("uvicorn").getChild("v1.auth.controllers.auth")


ROUTER = fastapi.APIRouter(tags=["auth"])

@ROUTER.post(
    "/login",
    summary="User login",
    response_model=auth_schema.LoginResponseSchema,
)
async def login(formData: OAuth2PasswordRequestForm = fastapi.Depends()) -> auth_schema.LoginResponseSchema:
    loginRequest = auth_schema.LoginRequestSchema(email=formData.username, password=formData.password)
    LOGGER.info("Intento de login para %s", loginRequest.email)
    return await auth_service.loginUser(loginRequest)


@ROUTER.get(
    "/session",
    summary="Validar sesión actual",
    response_model=auth_schema.SessionStatusResponseSchema,
)
async def getSessionStatus(request: Request) -> auth_schema.SessionStatusResponseSchema:
    sessionId = getattr(request.state, "authSessionId", None)
    if sessionId is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesión no encontrada o expirada.",
        )

    return await session_service.getSessionStatus(sessionId)


@ROUTER.post(
    "/refresh",
    summary="Refrescar tokens de sesión",
    response_model=auth_schema.LoginResponseSchema,
)
async def refreshTokens(request: auth_schema.RefreshRequestSchema) -> auth_schema.LoginResponseSchema:
    LOGGER.info("Solicitud de refresh de sesión recibida")
    return await auth_service.refreshSession(request)