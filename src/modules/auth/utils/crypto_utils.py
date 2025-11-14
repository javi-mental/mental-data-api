import logging

from cryptography.fernet import Fernet, InvalidToken

from src.config import ENVIRONMENT_CONFIG


LOGGER = logging.getLogger("uvicorn").getChild("v1.auth.utils.crypto")


class TokenCipherError(RuntimeError):
    """Error raised when upstream token encryption or decryption fails."""


_cipher_instance: Fernet | None = None


def _getCipher() -> Fernet:
    global _cipher_instance
    if _cipher_instance is not None:
        return _cipher_instance

    key = ENVIRONMENT_CONFIG.AUTH_CONFIG.UPSTREAM_TOKEN_ENCRYPTION_KEY
    if not key:
        raise TokenCipherError("UPSTREAM_TOKEN_ENCRYPTION_KEY no está configurado.")

    try:
        _cipher_instance = Fernet(key)
    except (ValueError, TypeError) as error:
        raise TokenCipherError("Clave de cifrado Fernet inválida.") from error

    return _cipher_instance


def encryptUpstreamToken(token: str) -> str:
    """Encrypt plain upstream tokens before storing them."""
    if token == "":
        return token
    cipher = _getCipher()
    return cipher.encrypt(token.encode("utf-8")).decode("utf-8")


def decryptUpstreamToken(token: str) -> str:
    """Decrypt upstream tokens retrieved from storage."""
    if token == "":
        return token
    cipher = _getCipher()
    try:
        return cipher.decrypt(token.encode("utf-8")).decode("utf-8")
    except InvalidToken as error:
        LOGGER.error("No se pudo descifrar el token upstream almacenado: %s", error)
        raise TokenCipherError("Token upstream cifrado inválido.") from error


__all__ = [
    "TokenCipherError",
    "decryptUpstreamToken",
    "encryptUpstreamToken",
]
