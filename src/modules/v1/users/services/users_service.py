import aiocache
import collections
import datetime
import typing
from src.modules.v1.shared.utils import dates as dates_utils
from ..repository import USERS_REPOSITORY
from ..schemas import user_schema
import anyio.to_thread

@aiocache.cached_stampede(
    lease=2,
    ttl=300,
    skip_cache_func=lambda count: count == 0,
)
async def _getUsersWithAURACount(
    isActive: bool,
    fromDate: int | None,
    toDate: int | None,
) -> int:

    count = await USERS_REPOSITORY.countUsersWithAURA(
        isActive=isActive,
        fromDate=fromDate,
        toDate=toDate,
    )

    return count



@aiocache.cached_stampede(
    lease=2,
    ttl=300,
)
async def _getUserByID(
    userID: str,
) -> user_schema.UserSchema | None:
    """
    Obtiene un usuario por su ID.
    """

    user = await USERS_REPOSITORY.getUserByID(userID=userID)
    return user



@aiocache.cached_stampede(
    lease=2,
    ttl=300,
    skip_cache_func=lambda userIDs: len(userIDs) == 0,
)
async def _getUsersByListOfIDs(
    userIDs: list[str],
) -> list[user_schema.UserSchema]:
    """
    Obtiene una lista de usuarios por sus IDs.
    """

    users = await USERS_REPOSITORY.getUsersByListOfIDs(userIDs=userIDs)

    return users



@aiocache.cached_stampede(
    lease=2,
    ttl=300,
    skip_cache_func=lambda count: count == 0,
)
async def _getUsersByHypnosisRequestCount(
    isActive: bool,
    fromDate: int | None,
    toDate: int | None,
) -> int:

    count = await USERS_REPOSITORY.countUsersByHypnosisRequest(
        isActive=isActive,
        fromDate=fromDate,
        toDate=toDate,
    )

    return count


getUsersByHypnosisRequestCount = typing.cast(
    typing.Callable[[bool, int | None, int | None], typing.Awaitable[int]],
    _getUsersByHypnosisRequestCount,
)


@aiocache.cached_stampede(
    lease=2,
    ttl=300,
)
async def _getUserPortals() -> list[int]:
    return await USERS_REPOSITORY.getDistinctPortals()

# Definimos los rangos de edad para la distribución
AGE_BUCKETS: tuple[tuple[str, int, int | None], ...] = (
    ("18-24", 18, 24),
    ("25-34", 25, 34),
    ("35-44", 35, 44),
    ("45-54", 45, 54),
    ("55-64", 55, 64),
    ("65+", 65, None),
)

# Edad por debajo de la cual se considera "menor de edad"
UNDERAGE_BUCKET = "0-17"

UNKNOWN_LABEL = "S/D"
UNKNOWN_AGE = UNKNOWN_LABEL


def _calculateAge(birthdate: str, reference: datetime.datetime) -> int | None:
    try:
        birthDatetime = dates_utils.parseISODatetime(birthdate)
    except ValueError:
        return None

    if birthDatetime.tzinfo is None:
        birthDatetime = birthDatetime.replace(tzinfo=datetime.timezone.utc)

    referenceUTC = reference.astimezone(datetime.timezone.utc)

    years = referenceUTC.year - birthDatetime.year
    hasHadBirthday = (
        (referenceUTC.month, referenceUTC.day)
        >= (birthDatetime.month, birthDatetime.day)
    )

    return years if hasHadBirthday else years - 1


def _resolveAgeBucket(age: int) -> str:
    if age < AGE_BUCKETS[0][1]:
        return UNDERAGE_BUCKET

    for bucketName, startAge, endAge in AGE_BUCKETS:
        if age < startAge:
            continue
        if endAge is None or age <= endAge:
            return bucketName

    return AGE_BUCKETS[-1][0]


def _buildPortalDistribution(
    portal: str,
    users: list[user_schema.UserSchema],
    fromDate: int | None,
    toDate: int | None,
) -> user_schema.UserPortalDistributionSchema:
    totalUsers = len(users)

    genreCounter: collections.Counter[str] = collections.Counter()
    ageCounter: collections.Counter[str] = collections.Counter()

    referenceDate = datetime.datetime.now(datetime.timezone.utc)

    for user in users:
        if user.gender:
            genreCounter[user.gender] += 1
        else:
            genreCounter[UNKNOWN_LABEL] += 1

        age = _calculateAge(user.birthdate, referenceDate)
        if age is None or age < 0:
            ageCounter[UNKNOWN_AGE] += 1
            continue

        bucket = _resolveAgeBucket(age)
        ageCounter[bucket] += 1

    # Ordenamos los buckets de edad para la salida
    # 0-17, 18-24, 25-34, ...
    orderedAgeBuckets: list[str] = [UNDERAGE_BUCKET] + [
        bucketName for bucketName, _, _ in AGE_BUCKETS
    ]

    ageDistribution : dict[str, int] = {}

    if ageCounter.get(UNKNOWN_AGE):
        ageDistribution[UNKNOWN_AGE] = ageCounter[UNKNOWN_AGE]

    for bucket in orderedAgeBuckets:
        if ageCounter.get(bucket):
            ageDistribution[bucket] = ageCounter[bucket]

    genreDistribution = dict(genreCounter)

    return user_schema.UserPortalDistributionSchema(
        portal=portal,
        totalUsers=totalUsers,
        genreDistribution=genreDistribution,
        ageDistribution=ageDistribution,
        fromDate=fromDate,
        toDate=toDate,
    )


@aiocache.cached_stampede(
    lease=2,
    ttl=300,
    skip_cache_func=lambda distribution: distribution.totalUsers == 0,
)
async def _getUserPortalDistribution(
    portal: str,
    fromDate: int | None,
    toDate: int | None,
) -> user_schema.UserPortalDistributionSchema:

    users = await USERS_REPOSITORY.getUsersByPortal(
        portal=portal,
        fromDate=fromDate,
        toDate=toDate,
    )

    return await anyio.to_thread.run_sync(
        _buildPortalDistribution,
        portal,
        users,
        fromDate,
        toDate,
    )




getUsersWithAURACount = typing.cast(
    typing.Callable[
        [bool, int | None, int | None], typing.Awaitable[int]
    ],
    _getUsersWithAURACount,
)


getUserByID = typing.cast(
    typing.Callable[
        [str], typing.Awaitable[user_schema.UserSchema | None]
    ],
    _getUserByID,
)


getUsersByListOfIDs = typing.cast(
    typing.Callable[
        [list[str]], typing.Awaitable[list[user_schema.UserSchema]]
    ],
    _getUsersByListOfIDs,
)


getUserPortalDistribution = typing.cast(
    typing.Callable[
        [str, int | None, int | None],
        typing.Awaitable[user_schema.UserPortalDistributionSchema],
    ],
    _getUserPortalDistribution,
)


getUserPortals = typing.cast(
    typing.Callable[[], typing.Awaitable[list[int]]],
    _getUserPortals,
)
