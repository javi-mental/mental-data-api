import typing
import fastapi
import logging
from ..schemas import suscribers_schema
from ..services import suscribers_service

LOGGER = logging.getLogger("uvicorn").getChild("v1.users.controllers.suscribers")


ROUTER = fastapi.APIRouter(
    prefix="/suscribers",
)


@ROUTER.get(
    "/count",
    summary="Obtener todos los suscriptores",
    response_class=fastapi.responses.JSONResponse,
    response_model=suscribers_schema.SuscribersSchema,
    responses={
        200: {"description": "Respuesta exitosa", "model": suscribers_schema.SuscribersSchema},
        400: {"description": "Solicitud inválida"},
        500: {"description": "Error interno del servidor"},
    },
)
async def getSuscribers(
    isActive: typing.Annotated[bool, fastapi.Query()] = True,
    fromDate: typing.Annotated[typing.Optional[int], fastapi.Query(description="Timestamp Unix (segundos, entero)")] = None,
    toDate: typing.Annotated[typing.Optional[int], fastapi.Query(description="Timestamp Unix (segundos, entero)")] = None,
) -> suscribers_schema.SuscribersSchema:
    """
    Obtiene el número de suscriptores según los filtros proporcionados.
    """

    # Ambas fechas deben ser provistas juntas o ninguna
    # El operador ^ es el XOR (o exclusivo)
    if (fromDate is None) ^ (toDate is None):
        raise fastapi.HTTPException(
            status_code=400,
            detail="Los parámetros fromDate y toDate deben proporcionarse juntos o no incluirse.",
        )
    
    if fromDate is not None and toDate is not None and toDate < fromDate:
        raise fastapi.HTTPException(
            status_code=400,
            detail="El parámetro toDate debe ser mayor o igual que fromDate.",
        )
        
    LOGGER.info(
        f"Obteniendo suscriptores con isActive={isActive}, fromDate={fromDate}, toDate={toDate}"
    )    

    count = await suscribers_service.getAllSuscribersCount(
        isActive=isActive,
        fromDate=fromDate,
        toDate=toDate,
    )

    LOGGER.info(
        f"Se encontraron {count} suscriptores con isActive={isActive}, fromDate={fromDate}, toDate={toDate}"
    )

    return suscribers_schema.SuscribersSchema(count=count, fromDate=fromDate, toDate=toDate)