import aiocache
import typing
from ..repository import HYPNOSIS_REPOSITORY
from ..schemas import audiorequest_schema


@aiocache.cached_stampede(
    lease=2,
    ttl=300,
    skip_cache_func=lambda count: count == 0,
)
async def _getAllHypnosisRequestsCount(
    fromDate: int | None,
    toDate: int | None,
) -> int:

    count = await HYPNOSIS_REPOSITORY.countAudioRequests(
        fromDate=fromDate,
        toDate=toDate,
    )

    return count


@aiocache.cached_stampede(
    lease=2,
    ttl=300,
    skip_cache_func=lambda count: count == 0,
)
async def _getNotListenedHypnosisRequestsCount(
    fromDate: int | None,
    toDate: int | None,
) -> int:

    count = await HYPNOSIS_REPOSITORY.countNotListenedAudioRequests(
        fromDate=fromDate,
        toDate=toDate,
    )

    return count


@aiocache.cached_stampede(
    lease=2,
    ttl=300,
)
async def _getAllHypnosisRequests(
    fromDate: int | None,
    toDate: int | None,
) -> list[audiorequest_schema.AudioRequestSchema]:

    requests = await HYPNOSIS_REPOSITORY.getAllAudioRequests(
        fromDate=fromDate,
        toDate=toDate,
    )

    return requests

@aiocache.cached_stampede(
    lease=2,
    ttl=300,
)
async def _getHypnosisRequestByID(
    requestID: str,
) -> audiorequest_schema.AudioRequestSchema | None:

    request = await HYPNOSIS_REPOSITORY.getAudioRequestByID(requestID=requestID)

    return request


@aiocache.cached_stampede(
    lease=2,
    ttl=300,
)
async def _getHypnosisRequestsByListOfIDs(
    requestIDs: list[str],
) -> list[audiorequest_schema.AudioRequestSchema]:

    requests = await HYPNOSIS_REPOSITORY.getAudioRequestsByListOfIDs(requestIDs=requestIDs)

    return requests


getAllHypnosisRequestsCount = typing.cast(
    typing.Callable[
        [int | None, int | None],
        typing.Awaitable[int],
    ],
    _getAllHypnosisRequestsCount,
)

getNotListenedHypnosisRequestsCount = typing.cast(
    typing.Callable[[int | None, int | None], typing.Awaitable[int]],
    _getNotListenedHypnosisRequestsCount,
)

getAllHypnosisRequests = typing.cast(
    typing.Callable[
        [int | None, int | None],
        typing.Awaitable[list[audiorequest_schema.AudioRequestSchema]],
    ],
    _getAllHypnosisRequests,
)

getHypnosisRequestByID = typing.cast(
    typing.Callable[
        [str],
        typing.Awaitable[audiorequest_schema.AudioRequestSchema | None],
    ],
    _getHypnosisRequestByID,
)


getHypnosisRequestsByListOfIDs = typing.cast(
    typing.Callable[
        [list[str]],
        typing.Awaitable[list[audiorequest_schema.AudioRequestSchema]],
    ],
    _getHypnosisRequestsByListOfIDs,
)