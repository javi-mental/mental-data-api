import datetime
import typing

import pydantic_mongo
import pymongo

from src.config import ENVIRONMENT_CONFIG
from ..schemas import auth_schema


class AuthSessionsRepository(pydantic_mongo.AsyncAbstractRepository[auth_schema.AuthSessionSchema]):
    class Meta:
        collection_name = ENVIRONMENT_CONFIG.AUTH_CONFIG.SESSION_COLLECTION_NAME

    async def createSession(self, session: auth_schema.AuthSessionSchema) -> auth_schema.AuthSessionSchema:
        now = datetime.datetime.now(datetime.timezone.utc)
        session.lastAccessAt = session.lastAccessAt or now
        result = await self.save(session)
        session.id = result.inserted_id
        return session

    async def trimSessionsForUser(
        self,
        user: dict[str, typing.Any],
        maxSessions: int,
    ) -> int:
        if not user:
            return 0

        filters: list[dict[str, typing.Any]] = []
        for key in ("_id", "id", "email"):
            value = user.get(key)
            if value:
                filters.append({f"user.{key}": value})

        if not filters:
            return 0

        normalizedMax = max(maxSessions, 0)

        query = {"$or": filters}

        if normalizedMax == 0:
            deleteResult = await self.get_collection().delete_many(query)
            return deleteResult.deleted_count

        cursor = (
            self.get_collection()
            .find(query, {"_id": 1})
            .sort("issuedAt", pymongo.DESCENDING)
            .skip(normalizedMax)
        )

        obsoleteSessions = await cursor.to_list(length=None)
        sessionIds = [session.get("_id") for session in obsoleteSessions if session.get("_id") is not None]

        if not sessionIds:
            return 0

        deleteResult = await self.get_collection().delete_many({"_id": {"$in": sessionIds}})
        return deleteResult.deleted_count

    async def getSessionBySessionId(self, sessionId: str) -> auth_schema.AuthSessionSchema | None:
        document = await self.get_collection().find_one({"sessionId": sessionId})
        if document is None:
            return None
        return auth_schema.AuthSessionSchema.model_validate(document)

    async def updateSessionAccess(
        self,
        sessionId: str,
        timestamp: datetime.datetime,
    ) -> None:
        await self.get_collection().update_one(
            {"sessionId": sessionId},
            {
                "$set": {
                    "lastAccessAt": timestamp,
                    "updatedAt": timestamp,
                }
            },
        )

    async def updateSessionTokens(
        self,
        sessionId: str,
        sessionTokenHash: str,
        refreshTokenHash: str,
        upstreamAccessToken: str,
        upstreamRefreshToken: str,
        accessExpiresAt: datetime.datetime | None,
        refreshExpiresAt: datetime.datetime | None,
        timestamp: datetime.datetime,
    ) -> None:
        await self.get_collection().update_one(
            {"sessionId": sessionId},
            {
                "$set": {
                    "issuedAt": timestamp,
                    "sessionTokenHash": sessionTokenHash,
                    "refreshTokenHash": refreshTokenHash,
                    "upstreamAccessToken": upstreamAccessToken,
                    "upstreamRefreshToken": upstreamRefreshToken,
                    "accessExpiresAt": accessExpiresAt,
                    "refreshExpiresAt": refreshExpiresAt,
                    "lastAccessAt": timestamp,
                    "updatedAt": timestamp,
                }
            },
        )


AUTH_MONGO_CLIENT = pymongo.AsyncMongoClient(
    ENVIRONMENT_CONFIG.CONNECTIONS_CONFIG.MONGO_DATABASE_URL
)

AUTH_SESSIONS_REPOSITORY = AuthSessionsRepository(
    database=AUTH_MONGO_CLIENT[ENVIRONMENT_CONFIG.AUTH_CONFIG.SESSION_DATABASE_NAME]
)