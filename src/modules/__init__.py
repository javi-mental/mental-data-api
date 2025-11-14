from .v1 import ROUTER as V1_ROUTER
from .auth import ROUTER as AUTH_ROUTER

ALL_MODULE_ROUTERS = [
    V1_ROUTER,
    AUTH_ROUTER,
]