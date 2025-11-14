import pydantic_mongo
import pymongo
from src.config import ENVIRONMENT_CONFIG
from src.modules.v1.shared.utils import dates as dates_utils
from ..schemas import user_schema
import logging
import typing

LOGGER = logging.getLogger("uvicorn").getChild("v1.users.repository.users")


class UsersRepository(
    pydantic_mongo.AsyncAbstractRepository[user_schema.UserSchema]
):
    class Meta:
        collection_name = ENVIRONMENT_CONFIG.USERS_CONFIG.USER_COLLECTION_NAME

    async def countSuscribers(
        self,
        isActive: bool,
        fromDate: int | None,
        toDate: int | None,
    ) -> int:
        """
        Calcula el total de suscriptores activos o inactivos usando una
        agregación que replica la lógica del dashboard.

        El calculo es:
        - Un suscriptor es activo si:
            - lastMembership.membershipPaymentDate existe y es menor o igual a hoy
            - El billingDate (o calculado a partir de membershipDate + 31 días)
              es mayor o igual a hoy
        por lo tal:
        membershipPaymentDate <= hoy <= billingDate
        """

        pipeline: list[dict[str, typing.Any]] = [
            {
                "$addFields": {
                    "payDate": {
                        "$convert": {
                            "input": "$lastMembership.membershipPaymentDate",
                            "to": "date",
                            "onError": None,
                            "onNull": None,
                        }
                    },
                    "rawBillingDate": {
                        "$convert": {
                            "input": "$lastMembership.billingDate",
                            "to": "date",
                            "onError": None,
                            "onNull": None,
                        }
                    },
                    "membershipDateConverted": {
                        "$convert": {
                            "input": "$lastMembership.membershipDate",
                            "to": "date",
                            "onError": None,
                            "onNull": None,
                        }
                    },
                }
            },
            {
                "$addFields": {
                    "billDate": {
                        "$cond": {
                            "if": {"$ne": ["$rawBillingDate", None]},
                            "then": "$rawBillingDate",
                            "else": {
                                "$cond": {
                                    "if": {"$ne": ["$membershipDateConverted", None]},
                                    "then": {
                                        "$dateAdd": {
                                            "startDate": "$membershipDateConverted",
                                            "unit": "day",
                                            "amount": 31,
                                        }
                                    },
                                    "else": None,
                                }
                            },
                        }
                    }
                }
            },
        ]

        if fromDate is not None and toDate is not None:
            fromDateParsed = dates_utils.timestampToDatetime(fromDate)
            toDateParsed = dates_utils.timestampToDatetime(toDate)

            pipeline.append(
                {
                    "$match": {
                        "$expr": {
                            "$and": [
                                {"$ne": ["$payDate", None]},
                                {"$gte": ["$payDate", fromDateParsed]},
                                {"$lte": ["$payDate", toDateParsed]},
                            ]
                        }
                    }
                }
            )

        activeConditions: list[dict[str, typing.Any]] = [
            {"$ne": ["$payDate", None]},
            {"$ne": ["$billDate", None]},
            {"$lte": ["$payDate", "$$NOW"]},
            {"$gte": ["$billDate", "$$NOW"]},
        ]

        if isActive:
            statusExpr: dict[str, typing.Any] = {"$and": activeConditions}
        else:
            statusExpr = {"$not": [{"$and": activeConditions}]}

        pipeline.append(
            {
                "$match": {
                    "lastMembership.type": {"$in": ["monthly", "yearly"]},
                    "$expr": statusExpr,
                }
            }
        )

        pipeline.append({"$count": "total"})

        cursor = await self.get_collection().aggregate(pipeline)
        result = await cursor.to_list(length=1)
        count = int(result[0]["total"]) if result else 0

        LOGGER.info(
            "Se contaron %s suscriptores usando la agregación: %s",
            count,
            pipeline,
        )

        return count

    async def countUsersByHypnosisRequest(
        self,
        isActive: bool,
        fromDate: int | None,
        toDate: int | None,
    ) -> int:
        """
        Cuenta usuarios según hayan generado (activos) o no (inactivos) una
        solicitud de hipnosis en el rango proporcionado.

        Sin rango de fechas se evalúa históricamente.
        """

        lookupConditions: list[dict[str, typing.Any]] = [
            {"$eq": ["$userId", "$$userId"]},
        ]

        if fromDate is not None and toDate is not None:
            fromDateParsed = dates_utils.timestampToDatetime(fromDate)
            toDateParsed = dates_utils.timestampToDatetime(toDate)

            createdAtAsDate = {
                "$convert": {
                    "input": "$createdAt",
                    "to": "date",
                    "onError": None,
                    "onNull": None,
                }
            }

            lookupConditions.extend(
                [
                    {"$gte": [createdAtAsDate, fromDateParsed]},
                    {"$lte": [createdAtAsDate, toDateParsed]},
                ]
            )

        lookupPipeline: list[dict[str, typing.Any]] = [
            {
                "$match": {
                    "$expr": {
                        "$and": lookupConditions,
                    }
                }
            },
            {"$limit": 1},
        ]

        pipeline: list[dict[str, typing.Any]] = [
            {
                "$lookup": {
                    "from": ENVIRONMENT_CONFIG.HYPNOSIS_CONFIG.HYPNOSIS_COLLECTION_NAME,
                    "let": {"userId": {"$toString": "$_id"}},
                    "pipeline": lookupPipeline,
                    "as": "audioRequests",
                }
            }
        ]

        if isActive:
            pipeline.append({"$match": {"audioRequests": {"$ne": []}}})
        else:
            pipeline.append({"$match": {"audioRequests": {"$eq": []}}})

        pipeline.append({"$count": "count"})

        cursor = await self.get_collection().aggregate(pipeline)
        result = await cursor.to_list(length=1)
        if result:
            return typing.cast(int, result[0]["count"])
        return 0

    async def getUsersByPortal(
        self,
        portal: str,
        fromDate: int | None,
        toDate: int | None,
    ) -> list[user_schema.UserSchema]:
        """
        Obtiene los usuarios pertenecientes a un portal específico.

        Permite filtrar por rango de fechas utilizando createdAt.
        """

        queryFilters: list[dict[str, typing.Any]] = [
            {"userLevel": str(portal)},
        ]

        if fromDate is not None and toDate is not None:
            fromDateParsed = dates_utils.timestampToDatetime(fromDate)
            toDateParsed = dates_utils.timestampToDatetime(toDate)

            queryFilters.append(
                {
                    "createdAt": {
                        "$gte": fromDateParsed,
                        "$lte": toDateParsed,
                    }
                }
            )

        if len(queryFilters) == 1:
            query: dict[str, typing.Any] = queryFilters[0]
        else:
            query = {"$and": queryFilters}

        cursor = await self.find_by_with_output_type(
            query=query,
            output_type=user_schema.UserSchema,
        )

        documents: list[dict[str, typing.Any]] = []
        
        for document in cursor:
            documents.append(document)
        
        LOGGER.info(
            f"Se obtuvieron {len(documents)} usuarios del portal '{portal}' con la consulta: {query}"
        )

        return documents

    async def countUsersWithAURA(
        self,
        isActive: bool,
        fromDate: int | None,
        toDate: int | None,
    ) -> int:
        """
        Cuenta los usuarios que tienen AURA habilitado.
        """

        queryFilters = []

        if isActive:
            queryFilters.append({"auraEnabled": True})
        else:
            queryFilters.append({"auraEnabled": False})

        if fromDate is not None and toDate is not None:
            fromDateParsed = dates_utils.timestampToDatetime(fromDate)
            toDateParsed = dates_utils.timestampToDatetime(toDate)

            queryFilters.append(
                {
                    "createdAt": {
                        "$gte": fromDateParsed,
                        "$lte": toDateParsed,
                    }
                }
            )

        if not queryFilters:
            query: dict[str, object] = {}
        elif len(queryFilters) == 1:
            query = queryFilters[0]
        else:
            query = {"$and": queryFilters}

        count = await self.get_collection().count_documents(query)
        LOGGER.info(
            f"Se contaron {count} usuarios con AURA usando la consulta: {query}"
        )
        return count

    async def getDistinctPortals(self) -> list[int]:
        values = await self.get_collection().distinct("userLevel")
        portals: list[int] = []

        for value in values:
            if value is None:
                continue
            try:
                portals.append(int(value))
            except (TypeError, ValueError):
                LOGGER.warning("Valor userLevel no numérico ignorado: %s", value)

        portals.sort()
        LOGGER.info("Se encontraron %s portales distintos: %s", len(portals), portals)
        return portals

USERS_MONGO_CLIENT = pymongo.AsyncMongoClient(
    ENVIRONMENT_CONFIG.CONNECTIONS_CONFIG.MONGO_DATABASE_URL
)

USERS_REPOSITORY = UsersRepository(
    database=USERS_MONGO_CLIENT[
        ENVIRONMENT_CONFIG.USERS_CONFIG.USER_DATABASE_NAME
    ]
)