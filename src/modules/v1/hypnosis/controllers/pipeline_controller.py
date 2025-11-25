import typing
import logging
import hmac

from fastapi import (
    APIRouter,
    Body,
    Depends,
    Request,
    WebSocket,
    WebSocketDisconnect,
    Query,
    Path,
    Header,
    HTTPException,
    status,
)

from src.config import ENVIRONMENT_CONFIG
from src.modules.v1.hypnosis.services.pipeline_service import PipelineService
from src.modules.v1.hypnosis.schemas.pipeline_schema import LoggingEventsResponse, RemainingTasksResponse, LoggingSchema
from src.modules.v1.hypnosis.services import pipeline_events_stream_service

router = APIRouter(prefix="/pipeline", tags=["Hypnosis Pipeline"])
webhookLogger = logging.getLogger("uvicorn").getChild("v1.hypnosis.pipeline.webhook")

def getPipelineService() -> PipelineService:
    return PipelineService(ENVIRONMENT_CONFIG)

@router.get("/logging/events", response_model=LoggingEventsResponse)
async def getLoggingEvents(
    fromDate: int = Query(..., description="Start of the time range (Unix timestamp in seconds)."),
    toDate: int = Query(..., description="End of the time range (Unix timestamp in seconds)."),
    eventType: typing.Annotated[typing.Optional[str], Query(description="Type of logging event to filter by.")] = None,
    service: PipelineService = Depends(getPipelineService)
):
    return await service.getLoggingEvents(fromDate=fromDate, toDate=toDate, eventType=eventType)

@router.get("/{artifact}/tasks/count-remaining", response_model=RemainingTasksResponse)
async def getRemainingTasks(
    artifact: str = Path(..., description="Artifact identifier (maker, export, decorator)."),
    service: PipelineService = Depends(getPipelineService)
):
    return await service.getRemainingTasks(artifact=artifact)

@router.websocket("/logging/ws")
async def websocketLoggingProxy(
    websocket: WebSocket,
    artifact: typing.Annotated[
        typing.Optional[str],
        Query(description="Artifact to observe in realtime (omit to receive all events)."),
    ] = None,
    skipSnapshot: bool = Query(
        default=False,
        description="Cuando es true, omite el envío inicial de eventos recientes.",
    ),
):
    filterKey = pipeline_events_stream_service.normalizeArtifactFilter(artifact)
    await websocket.accept()
    await pipeline_events_stream_service.registerConnection(filterKey, websocket)

    if not skipSnapshot:
        snapshot = await pipeline_events_stream_service.snapshotEvents(filterKey)
        for item in snapshot:
            await websocket.send_json(item.model_dump(mode="json", by_alias=True, round_trip=True))

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        logging.getLogger("uvicorn").getChild("v1.hypnosis.pipeline.ws").info(
            "Client disconnected from logging websocket",
        )
        await pipeline_events_stream_service.removeConnection(filterKey, websocket)
    except Exception:
        logging.getLogger("uvicorn").getChild("v1.hypnosis.pipeline.ws").exception(
            "Unexpected error in websocket connection",
        )
        await pipeline_events_stream_service.removeConnection(filterKey, websocket)
        raise


@router.post(
    "/logging/events/webhook",
    status_code=status.HTTP_202_ACCEPTED,
)
async def receiveLoggingEventWebhook(
    request: Request,
    event: typing.Annotated[LoggingSchema, Body(...)],
    signature: str = Header(..., alias="x-hypnosis-signature"),
) -> dict[str, str]:
    expectedSignature = (
        ENVIRONMENT_CONFIG.HYPNOSIS_CONFIG.HYPNOSIS_WEBHOOK_SIGNATURE_SECRET
    )
    clientHost = request.client.host if request and request.client else "unknown"
    if not expectedSignature:
        webhookLogger.error(
            "Webhook rejected: missing expected signature secret | client=%s | receivedSignature=%s",
            clientHost,
            signature,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Webhook signature secret is not configured.",
        )
    if not hmac.compare_digest(signature, expectedSignature):
        webhookLogger.warning(
            "Webhook signature mismatch | client=%s | artifact=%s | eventType=%s | audioRequestId=%s | expectedSignature=%s | receivedSignature=%s",
            clientHost,
            event.receivedArtifact,
            event.eventType,
            event.audioRequestID,
            expectedSignature,
            signature,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature.",
        )

    webhookLogger.debug(
        "Webhook accepted | client=%s | artifact=%s | eventType=%s | audioRequestId=%s",
        clientHost,
        event.receivedArtifact,
        event.eventType,
        event.audioRequestID,
    )
    await pipeline_events_stream_service.dispatchRealtimeEvent(event)
    return {"message": "Webhook event accepted"}
