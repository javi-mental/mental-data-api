import pydantic_settings
import pydantic

class HypnosisConfig(pydantic_settings.BaseSettings):
    
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


    
    HYPNOSIS_DATABASE_NAME: str = pydantic.Field(
        default="mmg",
        description="Nombre de la base de datos utilizada para hipnosis.",
    )

    HYPNOSIS_COLLECTION_NAME: str = pydantic.Field(
        default="audio-requests",
        description="Nombre de la colección donde se guardan las solicitudes de audio.",
    )

    HYPNOSIS_API_URL: str = pydantic.Field(
        default="http://localhost:8000",
        description="URL de la API de hipnosis.",
    )

    HYPNOSIS_API_KEY: str = pydantic.Field(
        default="",
        description="API Key para la API de hipnosis.",
    )

    HYPNOSIS_WEBHOOK_SIGNATURE_SECRET: str = pydantic.Field(
        ...,
        description="Secreto compartido para validar webhooks recibidos de Hypnosis.",
    )

    HYPNOSIS_WS_URL: str = pydantic.Field(
        default="ws://localhost:8000",
        description="URL del WebSocket de la API de hipnosis.",
    )