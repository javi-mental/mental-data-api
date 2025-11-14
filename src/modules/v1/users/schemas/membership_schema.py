import pydantic


class MembershipSchema(pydantic.BaseModel):

    model_config = pydantic.ConfigDict(
        extra="ignore",
        validate_by_alias=True,
        validate_by_name=True,
        serialize_by_alias=True,
    )

    membershipId: str = pydantic.Field(
        ...,
        description="Identificador único de la membresía.",
    )

    membershipDate: str = pydantic.Field(
        ...,
        description="Fecha en la que se creó la membresía.",
    )

    membershipPaymentDate: str = pydantic.Field(
        default="",
        description="Fecha de vencimiento del pago de la membresía.",
    )

    type: str = pydantic.Field(
        ...,
        description="Tipo de membresía.",
    )