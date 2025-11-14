import pydantic
import typing

class SuscribersSchema(pydantic.BaseModel):

    model_config = pydantic.ConfigDict(
        extra="ignore",
        validate_by_alias=True,
        validate_by_name=True,
        serialize_by_alias=True,
    )

    count: int = pydantic.Field(
        ...,
        description="Cantidad de suscriptores."
    )

    fromDate: typing.Optional[int] = pydantic.Field(
        default=None,
        description="Timestamp inicial (segundos Unix) utilizado en el filtrado de suscriptores.",
    )

    toDate: typing.Optional[int] = pydantic.Field(
        default=None,
        description="Timestamp final (segundos Unix) utilizado en el filtrado de suscriptores.",
    )