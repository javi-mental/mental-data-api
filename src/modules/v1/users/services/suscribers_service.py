import aiocache
import typing
from ..repository import USERS_REPOSITORY


@aiocache.cached_stampede(
    lease=2,
    ttl=300,
    skip_cache_func=lambda count: count == 0,
)
async def _getAllSuscribersCount(
    isActive: bool,
    fromDate: int | None,
    toDate: int | None,
) -> int:

    count = await USERS_REPOSITORY.countSuscribers(
        isActive=isActive,
        fromDate=fromDate,
        toDate=toDate,
    )

    return count

getAllSuscribersCount = typing.cast(
    typing.Callable[
        [bool, int | None, int | None], typing.Awaitable[int]
    ],
    _getAllSuscribersCount,
)
