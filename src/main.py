import fastapi
import sentry_sdk
from guard.middleware import SecurityMiddleware
from guard.models import SecurityConfig

from .config import ENVIRONMENT_CONFIG
from .modules import ALL_MODULE_ROUTERS
from .modules.auth.guards.token_guard import verifyAccessToken

sentry_sdk.init(
    dsn=ENVIRONMENT_CONFIG.SENTRY_CONFIG.SENTRY_DSN,
    send_default_pii=True,
    traces_sample_rate=ENVIRONMENT_CONFIG.SENTRY_CONFIG.SENTRY_SAMPLE_RATE,
    environment=ENVIRONMENT_CONFIG.SENTRY_CONFIG.SENTRY_ENVIRONMENT,
    release=ENVIRONMENT_CONFIG.SENTRY_CONFIG.SENTRY_RELEASE,
    enable_logs=ENVIRONMENT_CONFIG.SENTRY_CONFIG.SENTRY_ENABLE_LOGS
)

APP = fastapi.FastAPI(
    title="MENTAL DATA API" + " - " + ENVIRONMENT_CONFIG.SENTRY_CONFIG.SENTRY_ENVIRONMENT,
    version=ENVIRONMENT_CONFIG.SENTRY_CONFIG.SENTRY_RELEASE,
    description="Aplicación FastAPI para el procesamiento de datos de Mental",
)

securityConfig = SecurityConfig(
    custom_request_check=verifyAccessToken,
    rate_limit=ENVIRONMENT_CONFIG.AUTH_CONFIG.GUARD_RATE_LIMIT,
    rate_limit_window=ENVIRONMENT_CONFIG.AUTH_CONFIG.GUARD_RATE_LIMIT_WINDOW_SECONDS,
)

APP.add_middleware(SecurityMiddleware, config=securityConfig)

for router in ALL_MODULE_ROUTERS:
    APP.include_router(router)