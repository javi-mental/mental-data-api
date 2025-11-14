import pydantic_settings
import pydantic

from .users_config import UsersConfig
from .sentry_config import SentryConfig
from .hypnosis_config import HypnosisConfig
from .connections_config import ConnectionsConfig
from .auth_config import AuthConfig

class EnvironmentConfig(pydantic_settings.BaseSettings):

    model_config = pydantic_settings.SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=False,
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        validate_by_alias=True,
        validate_by_name=True,
        serialize_by_alias=True
    )

    USERS_CONFIG: UsersConfig = pydantic.Field(
        default_factory=UsersConfig,
        description="Configuración del módulo de usuarios.",
    )

    SENTRY_CONFIG: SentryConfig = pydantic.Field(
        default_factory=SentryConfig,
        description="Configuración del monitoreo de errores con Sentry.",
    )

    HYPNOSIS_CONFIG: HypnosisConfig = pydantic.Field(
        default_factory=HypnosisConfig,
        description="Configuración del módulo de hipnosis.",
    )

    CONNECTIONS_CONFIG: ConnectionsConfig = pydantic.Field(
        default_factory=ConnectionsConfig,
        description="Configuración de las conexiones a bases de datos.",
    )

    AUTH_CONFIG: AuthConfig = pydantic.Field(
        default_factory=AuthConfig,
        description="Configuración de la integración de autenticación upstream.",
    )