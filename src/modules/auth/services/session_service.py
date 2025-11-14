from fastapi import HTTPException, status

from ..repository import auth_repository
from ..schemas import auth_schema


async def getSessionStatus(sessionId: str) -> auth_schema.SessionStatusResponseSchema:
    session = await auth_repository.AUTH_SESSIONS_REPOSITORY.getSessionBySessionId(sessionId)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesión no encontrada o expirada.",
        )

    return auth_schema.SessionStatusResponseSchema(
        sessionId=session.sessionId,
        user=session.user,
        issuedAt=session.issuedAt,
        lastAccessAt=session.lastAccessAt,
        accessExpiresAt=session.accessExpiresAt,
        refreshExpiresAt=session.refreshExpiresAt,
    )
