import fastapi
from src.modules.auth.security import oauth2Scheme
from .users import ROUTER as USERS_ROUTER
from .hypnosis import ROUTER as HYPNOSIS_ROUTER


ROUTER = fastapi.APIRouter(
    tags=["v1"],
    prefix="/v1",
    dependencies=[fastapi.Depends(oauth2Scheme)],
)

ROUTER.include_router(
    USERS_ROUTER
)

ROUTER.include_router(
    HYPNOSIS_ROUTER
)