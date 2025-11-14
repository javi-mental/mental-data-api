import logging

import pydantic_mongo
import pymongo

from src.config import ENVIRONMENT_CONFIG
from src.modules.v1.shared.utils import dates as dates_utils
from ..schemas import audiorequest_schema

LOGGER = logging.getLogger("uvicorn").getChild("v1.hypnosis.repository.hypnosis")


class HypnosisRepository(
    pydantic_mongo.AbstractRepository[audiorequest_schema.AudioRequestSchema]
):
    class Meta:
        collection_name = ENVIRONMENT_CONFIG.HYPNOSIS_CONFIG.HYPNOSIS_COLLECTION_NAME

    async def countAudioRequests(
        self,
        fromDate: int | None,
        toDate: int | None,
    ) -> int:
        """
        Cuenta todas las solicitudes de audio en el rango de fechas proporcionado.

        Al no proveer un rango de fechas, se cuentan todas las solicitudes de audio.
        """

        queryFilters = []

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

        if queryFilters:
            finalQuery = {"$and": queryFilters}
        else:
            finalQuery = {}

        count : int = await self.get_collection().count_documents(finalQuery)
        return count

    async def countNotListenedAudioRequests(
        self,
        fromDate: int | None,
        toDate: int | None,
    ) -> int:
        """
        Cuenta las solicitudes de audio marcadas como no escuchadas (isAvailable = True).
        """

        queryFilters = [
            {"isAvailable": True},
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
            finalQuery = queryFilters[0]
        else:
            finalQuery = {"$and": queryFilters}

        count: int = await self.get_collection().count_documents(finalQuery)
        return count


HYPNOSIS_MONGO_CLIENT = pymongo.AsyncMongoClient(
    ENVIRONMENT_CONFIG.CONNECTIONS_CONFIG.MONGO_DATABASE_URL
)

HYPNOSIS_REPOSITORY = HypnosisRepository(
    database=HYPNOSIS_MONGO_CLIENT[
        ENVIRONMENT_CONFIG.HYPNOSIS_CONFIG.HYPNOSIS_DATABASE_NAME
    ]
)