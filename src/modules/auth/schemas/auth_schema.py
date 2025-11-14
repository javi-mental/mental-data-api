import datetime
import typing

import pydantic
from pydantic import computed_field
import pydantic_mongo


class LoginRequestSchema(pydantic.BaseModel):
    """Cuerpo esperado para el inicio de sesión."""

    email: pydantic.EmailStr = pydantic.Field(
        description="Correo electrónico utilizado para autenticarse.",
    )
    password: str = pydantic.Field(
        min_length=8,
        description="Contraseña en texto plano enviada a través de un canal TLS.",
    )


class UpstreamTokenPairSchema(pydantic.BaseModel):
    """Respuesta esperada del servidor upstream."""

    accessToken: str = pydantic.Field(..., alias="access_token", description="Access token emitido por el servidor upstream.")
    refreshToken: str = pydantic.Field(..., alias="refresh_token", description="Refresh token emitido por el servidor upstream.")
    
    user: dict[str, typing.Any] = pydantic.Field(
        default_factory=dict,
        description="Representación del usuario retornada por el servidor upstream.",
    )

    expiresIn: int | None = pydantic.Field(
        alias="expires_in",
        default=None,
        description="Tiempo de vida del access token en segundos (opcional).",
    )

    refreshExpiresIn: int | None = pydantic.Field(
        alias="refresh_expires_in",
        default=None,
        description="Tiempo de vida del refresh token en segundos (opcional).",
    )


class LoginResponseSchema(pydantic.BaseModel):
    """Respuesta propia de la API tras derivar los tokens."""

    accessToken: str = pydantic.Field(description="Token firmado por nuestra API para autenticación subsecuente.")
    refreshToken: str = pydantic.Field(description="Token de refresco firmado por nuestra API.")
    tokenType: str = pydantic.Field(default="bearer", description="Tipo de token que expone el flujo OAuth2.")
    user: dict[str, typing.Any] = pydantic.Field(
        default_factory=dict,
        description="Datos del usuario autenticado que exponemos al cliente.",
    )

    @computed_field(return_type=str, alias="access_token")
    def accessTokenOAuth(self) -> str:
        return self.accessToken

    @computed_field(return_type=str, alias="refresh_token")
    def refreshTokenOAuth(self) -> str:
        return self.refreshToken

    @computed_field(return_type=str, alias="token_type")
    def tokenTypeOAuth(self) -> str:
        return self.tokenType


class SessionStatusResponseSchema(pydantic.BaseModel):
    """Información básica de la sesión autenticada."""

    sessionId: str = pydantic.Field(description="Identificador de la sesión actual.")
    user: dict[str, typing.Any] = pydantic.Field(description="Datos del usuario autenticado.")
    issuedAt: datetime.datetime = pydantic.Field(description="Fecha y hora de emisión de la sesión.")
    lastAccessAt: datetime.datetime | None = pydantic.Field(default=None, description="Último acceso registrado.")
    accessExpiresAt: datetime.datetime | None = pydantic.Field(default=None, description="Fecha de expiración del access token.")
    refreshExpiresAt: datetime.datetime | None = pydantic.Field(default=None, description="Fecha de expiración del refresh token.")


class RefreshRequestSchema(pydantic.BaseModel):
    """Solicitud para refrescar tokens derivados."""

    refreshToken: str = pydantic.Field(description="Refresh token derivado emitido previamente.")


class AuthSessionSchema(pydantic.BaseModel):
    """Entidad almacenada en MongoDB para gestionar sesiones locales."""

    model_config = pydantic.ConfigDict(
        extra="ignore",
        validate_by_alias=True,
        validate_by_name=True,
        serialize_by_alias=True,
    )

    id: typing.Optional[pydantic_mongo.PydanticObjectId] = pydantic.Field(
        default=None,
        description="Identificador interno de la sesión.",
    )

    sessionId: str = pydantic.Field(
        description="Identificador de sesión generado por nuestra API.",
    )
    sessionTokenHash: str = pydantic.Field(
        description="Hash del token derivado que entregamos al cliente.",
    )
    refreshTokenHash: str = pydantic.Field(
        description="Hash del refresh token derivado.",
    )
    upstreamAccessToken: str = pydantic.Field(
        description="Access token del servidor upstream almacenado de forma cifrada.",
    )
    upstreamRefreshToken: str = pydantic.Field(
        description="Refresh token del servidor upstream almacenado de forma cifrada.",
    )
    user: dict[str, typing.Any] = pydantic.Field(
        default_factory=dict,
        description="Datos relevantes del usuario retornados por el upstream.",
    )
    issuedAt: datetime.datetime = pydantic.Field(
        description="Momento en el que se generó la sesión local.",
    )
    lastAccessAt: datetime.datetime | None = pydantic.Field(
        default=None,
        description="Último momento registrado en el que el token fue utilizado.",
    )
    accessExpiresAt: datetime.datetime | None = pydantic.Field(
        default=None,
        description="Momento en el que vence el access token local.",
    )
    refreshExpiresAt: datetime.datetime | None = pydantic.Field(
        default=None,
        description="Momento en el que vence el refresh token local.",
    )
    createdAt: datetime.datetime = pydantic.Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc),
        description="Fecha de creación del documento.",
    )
    updatedAt: datetime.datetime = pydantic.Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc),
        description="Fecha de la última actualización.",
    )