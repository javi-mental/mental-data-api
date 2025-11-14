import pydantic
import pydantic_settings


class AuthConfig(pydantic_settings.BaseSettings):
    """Configuración para la integración con el servidor de autenticación upstream."""

    model_config = pydantic_settings.SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=False,
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        validate_by_alias=True,
        validate_by_name=True,
        serialize_by_alias=True,
    )

    AUTH_BASE_URL: str = pydantic.Field(
        ...,
        description="URL base del servidor de autenticación upstream (por ejemplo https://auth.example.com/api).",
    )

    AUTH_TIMEOUT_SECONDS: float = pydantic.Field(
        default=10.0,
        description="Tiempo máximo (en segundos) para las solicitudes HTTP al servidor upstream.",
    )

    AUTH_LOGIN_ENDPOINT: str = pydantic.Field(
        default="/auth/login",
        description="Endpoint relativo para iniciar sesión en el servidor upstream.",
    )

    AUTH_REFRESH_ENDPOINT: str = pydantic.Field(
        default="/auth/refresh",
        description="Endpoint relativo para refrescar tokens en el servidor upstream.",
    )

    APP_AUTH_SECRET: str = pydantic.Field(
        default="",
        description="Secreto utilizado para firmar los tokens derivados que entrega nuestra API.",
    )

    APP_REFRESH_SECRET: str | None = pydantic.Field(
        default=None,
        description="Secreto opcional para firmar tokens de refresh propios si se desea separarlos.",
    )

    SESSION_DATABASE_NAME: str = pydantic.Field(
        default="mental-data",
        description="Nombre de la base de datos en MongoDB donde se almacenan las sesiones.",
    )

    SESSION_COLLECTION_NAME: str = pydantic.Field(
        default="sessions",
        description="Nombre de la colección donde se guardan las sesiones de autenticación.",
    )

    DERIVED_TOKEN_TTL_SECONDS: int = pydantic.Field(
        default=172_800,
        description="Duración máxima del token de acceso derivado (fallback) en segundos.",
    )

    SESSION_TTL_SECONDS: int = pydantic.Field(
        default=604_800,
        description="Tiempo máximo que almacenamos la sesión en Mongo antes de considerarla expirada (fallback para refresh).",
    )

    UPSTREAM_TOKEN_ENCRYPTION_KEY: str = pydantic.Field(
        ...,
        description=(
            "Clave en formato base64 compatible con Fernet utilizada para cifrar los tokens "
            "del servidor upstream almacenados en la base de datos."
        ),
    )

    GUARD_RATE_LIMIT: int = pydantic.Field(
        default=120,
        description="Cantidad máxima de solicitudes permitidas por ventana para toda la API.",
    )

    GUARD_RATE_LIMIT_WINDOW_SECONDS: int = pydantic.Field(
        default=60,
        description="Duración de la ventana de rate limiting global expresada en segundos.",
    )
