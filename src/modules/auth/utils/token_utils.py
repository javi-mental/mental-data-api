import base64
import datetime
import dataclasses
import hashlib
import hmac
import secrets


class TokenValidationError(RuntimeError):
    """Error raised when a derived token cannot be validated."""


@dataclasses.dataclass
class DerivedTokenData:
    sessionId: str
    issuedAt: datetime.datetime
    nonce: str
    signature: str
    payload: str


def buildDerivedToken(
    sessionId: str,
    upstreamToken: str,
    issuedAt: datetime.datetime,
    secret: str,
) -> str:
    nonce = secrets.token_hex(16)
    payload = f"{sessionId}.{issuedAt.isoformat()}.{nonce}"
    signature = _generateSignature(payload, upstreamToken, secret)
    return f"{payload}.{signature}"


def hashToken(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def parseDerivedToken(token: str) -> DerivedTokenData:
    parts = token.split(".")
    if len(parts) < 4:
        raise TokenValidationError("Token derivado con formato inválido.")

    sessionId = parts[0]
    signature = parts[-1]
    nonce = parts[-2]
    issuedAtRaw = ".".join(parts[1:-2])

    if not sessionId or not nonce or not signature or not issuedAtRaw:
        raise TokenValidationError("Token derivado incompleto.")

    try:
        issuedAt = datetime.datetime.fromisoformat(issuedAtRaw)
    except ValueError as error:
        raise TokenValidationError("Fecha de emisión inválida en el token derivado.") from error

    if issuedAt.tzinfo is None:
        issuedAt = issuedAt.replace(tzinfo=datetime.timezone.utc)

    payload = ".".join((sessionId, issuedAtRaw, nonce))

    return DerivedTokenData(
        sessionId=sessionId,
        issuedAt=issuedAt,
        nonce=nonce,
        signature=signature,
        payload=payload,
    )


def verifyDerivedToken(
    token: str,
    upstreamToken: str,
    secret: str,
    expectedSessionId: str | None = None,
) -> DerivedTokenData:
    tokenData = parseDerivedToken(token)

    if expectedSessionId is not None and tokenData.sessionId != expectedSessionId:
        raise TokenValidationError("El identificador de sesión no coincide con el token almacenado.")

    expectedSignature = _generateSignature(tokenData.payload, upstreamToken, secret)

    if not hmac.compare_digest(tokenData.signature, expectedSignature):
        raise TokenValidationError("Firma del token derivado inválida.")

    return tokenData


def _generateSignature(payload: str, upstreamToken: str, secret: str) -> str:
    digest = hmac.new(
        key=secret.encode(),
        msg=(payload + upstreamToken).encode(),
        digestmod=hashlib.sha256,
    ).digest()
    return base64.urlsafe_b64encode(digest).decode().rstrip("=")


__all__ = [
    "DerivedTokenData",
    "TokenValidationError",
    "buildDerivedToken",
    "hashToken",
    "parseDerivedToken",
    "verifyDerivedToken",
]