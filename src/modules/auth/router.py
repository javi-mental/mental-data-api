import fastapi

from . import controllers


ROUTER = fastapi.APIRouter(
    prefix="/auth",
    tags=["auth"],
)

for controller in controllers.ALL_CONTROLLERS:
    ROUTER.include_router(controller)