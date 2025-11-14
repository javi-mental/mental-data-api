import datetime
import typing


TimestampLike = typing.Union[int, float]


def timestampToDatetime(timestamp: TimestampLike) -> datetime.datetime:
    """Convierte un timestamp Unix (segundos) a datetime consciente de zona en UTC."""

    return datetime.datetime.fromtimestamp(float(timestamp), datetime.timezone.utc)


def datetimeToTimestamp(value: datetime.datetime) -> float:
    """Convierte un datetime a timestamp Unix (segundos)."""

    if value.tzinfo is None:
        value = value.replace(tzinfo=datetime.timezone.utc)
    return value.timestamp()


def parseISODatetime(
    dateString: str,
) -> datetime.datetime:
    """
    Convierte una cadena ISO 8601 (aceptando sufijo 'Z') a datetime aware.
    """

    normalized = dateString.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"

    try:
        return datetime.datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError(
            f"El valor proporcionado ({dateString}) no tiene formato ISO 8601 válido."
        ) from exc