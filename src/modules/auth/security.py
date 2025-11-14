"""Definitions of FastAPI security schemes used across the API."""

from fastapi.security import OAuth2PasswordBearer


# OAuth2 password flow so Swagger UI exposes the Authorize modal for bearer tokens.
oauth2Scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login",
    scopes={
        "default": "Acceso a los endpoints protegidos de la API.",
    },
)

__all__ = ["oauth2Scheme"]
