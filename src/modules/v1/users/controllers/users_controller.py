import typing
import fastapi
from ..schemas import user_schema
from ..services import users_service


ROUTER = fastapi.APIRouter()



@ROUTER.get(
    "/count/aura",
    summary="Obtener conteo de usuarios con AURA habilitado",
    response_class=fastapi.responses.JSONResponse,
    response_model=user_schema.UserCountSchema,
    responses={
    200: {"description": "Respuesta exitosa", "model": user_schema.UserCountSchema},
    400: {"description": "Solicitud inválida"},
    500: {"description": "Error interno del servidor"},
    },
)
async def getUsersWithAURA(
    isActive: typing.Annotated[bool, fastapi.Query()] = True,
    fromDate: typing.Annotated[typing.Optional[int], fastapi.Query(description="Timestamp Unix (segundos, entero)")] = None,
    toDate: typing.Annotated[typing.Optional[int], fastapi.Query(description="Timestamp Unix (segundos, entero)")] = None,
) -> user_schema.UserCountSchema:
    """
    Obtiene el número de usuarios con AURA habilitado según los filtros proporcionados.

    Al dar fechas, se obtiene los usuarios con aura que se han creado en ese rango de fechas.
    """

    # Ambas fechas deben ser provistas juntas o ninguna
    # El operador ^ es el XOR (o exclusivo)
    if (fromDate is None) ^ (toDate is None):
        raise fastapi.HTTPException(
            status_code=400,
            detail="fromDate y toDate deben proporcionarse juntas o no enviarse.",
        )
    
    if fromDate is not None and toDate is not None and toDate < fromDate:
        raise fastapi.HTTPException(
            status_code=400,
            detail="toDate debe ser mayor o igual que fromDate.",
        )

    count = await users_service.getUsersWithAURACount(
        isActive=isActive,
        fromDate=fromDate,
        toDate=toDate,
    )

    return user_schema.UserCountSchema(count=count , fromDate=fromDate, toDate=toDate)



@ROUTER.get(
    "/count/user-with-hypnosis-request",
    summary="Obtener conteo de usuarios por solicitudes de hipnosis",
    response_class=fastapi.responses.JSONResponse,
    response_model=user_schema.UserCountSchema,
    responses={
    200: {"description": "Respuesta exitosa", "model": user_schema.UserCountSchema},
    400: {"description": "Solicitud inválida"},
    500: {"description": "Error interno del servidor"},
    },
)
async def getUserHypnosisRequestCount(
    isActive: typing.Annotated[bool, fastapi.Query()] = True,
    fromDate: typing.Annotated[typing.Optional[int], fastapi.Query(description="Timestamp Unix (segundos, entero)")] = None,
    toDate: typing.Annotated[typing.Optional[int], fastapi.Query(description="Timestamp Unix (segundos, entero)")] = None,
) -> user_schema.UserCountSchema:
    """
    Si isActive es True cuenta usuarios con al menos una solicitud en el rango.
    Si es False cuenta los que no generaron ninguna.
    """

    # Ambas fechas deben ser provistas juntas o ninguna
    if (fromDate is None) ^ (toDate is None):
        raise fastapi.HTTPException(
            status_code=400,
            detail="fromDate y toDate deben proporcionarse juntas o no enviarse.",
        )

    if fromDate is not None and toDate is not None and toDate < fromDate:
        raise fastapi.HTTPException(
            status_code=400,
            detail="toDate debe ser mayor o igual que fromDate.",
        )

    count = await users_service.getUsersByHypnosisRequestCount(
        isActive=isActive,
        fromDate=fromDate,
        toDate=toDate,
    )

    return user_schema.UserCountSchema(count=count, fromDate=fromDate, toDate=toDate)


@ROUTER.get(
    "/portals",
    summary="Listar portales disponibles",
    response_class=fastapi.responses.JSONResponse,
    response_model=user_schema.UserPortalListSchema,
    responses={
    200: {"description": "Respuesta exitosa", "model": user_schema.UserPortalListSchema},
    500: {"description": "Error interno del servidor"},
    },
)
async def listUserPortals() -> user_schema.UserPortalListSchema:
    portals = await users_service.getUserPortals()
    return user_schema.UserPortalListSchema(portals=portals)


@ROUTER.get(
    "/distribution/portal",
    summary="Obtener distribución de usuarios por portal",
    response_class=fastapi.responses.JSONResponse,
    response_model=user_schema.UserPortalDistributionSchema,
    responses={
    200: {"description": "Respuesta exitosa", "model": user_schema.UserPortalDistributionSchema},
    400: {"description": "Solicitud inválida"},
    500: {"description": "Error interno del servidor"},
    },
)
async def getUserPortalDistribution(
    portal: typing.Annotated[str, fastapi.Query(description="Portal (userLevel) para el cual se calculará la distribución")],
    fromDate: typing.Annotated[typing.Optional[int], fastapi.Query(description="Timestamp Unix (segundos, entero)")] = None,
    toDate: typing.Annotated[typing.Optional[int], fastapi.Query(description="Timestamp Unix (segundos, entero)")] = None,
) -> user_schema.UserPortalDistributionSchema:
    """
    Obtiene la distribución de usuarios de un portal específico, agrupando por género y rangos de edad.
    """

    if not portal:
        raise fastapi.HTTPException(
            status_code=400,
            detail="El parámetro portal es obligatorio.",
        )

    if (fromDate is None) ^ (toDate is None):
        raise fastapi.HTTPException(
            status_code=400,
            detail="fromDate y toDate deben proporcionarse juntas o no enviarse.",
        )

    if fromDate is not None and toDate is not None and toDate < fromDate:
        raise fastapi.HTTPException(
            status_code=400,
            detail="toDate debe ser mayor o igual que fromDate.",
        )

    distribution = await users_service.getUserPortalDistribution(
        portal=portal,
        fromDate=fromDate,
        toDate=toDate,
    )

    return distribution


