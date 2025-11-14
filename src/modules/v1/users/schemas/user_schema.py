import pydantic
import pydantic_mongo
import typing
from .membership_schema import MembershipSchema

class UserSchema(pydantic.BaseModel):

    model_config = pydantic.ConfigDict(
        extra="ignore",
        validate_by_alias=True,
        validate_by_name=True,
        serialize_by_alias=True,
    )

    id : typing.Optional[pydantic_mongo.PydanticObjectId] = pydantic.Field(
        default=None,
        alias="_id",
        description="Identificador único del usuario.",
    )

    names: str = pydantic.Field(
        ...,
        description="Nombres del usuario.",
    )

    lastnames: str = pydantic.Field(
        ...,
        description="Apellidos del usuario.",
    )

    wantToBeCalled: str = pydantic.Field(
        ...,
        description="Nombre con el que el usuario prefiere ser llamado.",
    )

    email: str = pydantic.Field(
        ...,
        description="Correo electrónico del usuario.",
    )

    gender: str = pydantic.Field(
        ...,
        description="Género del usuario.",
    )

    birthdate: str = pydantic.Field(
        ...,
        description="Fecha de nacimiento del usuario.",
    )

    lastMembership: MembershipSchema = pydantic.Field(
        ...,
        description="Información de la última membresía del usuario.",
    )

    userLevel: str = pydantic.Field(
        ...,
        description="Nivel del usuario (corresponde al portal).",
    )

    features: typing.Dict[str, typing.Any] = pydantic.Field(
        default_factory=dict,
        description="Funcionalidades disponibles para el usuario.",
    )

    auraEnabled: bool = pydantic.Field(
        default=False,
        description="Indica si el aura del usuario está habilitada.",
    )

    language: str = pydantic.Field(
        default="es",
        description="Idioma preferido del usuario.",
    )

class UserCountSchema(pydantic.BaseModel):

    model_config = pydantic.ConfigDict(
        extra="ignore",
        validate_by_alias=True,
        validate_by_name=True,
        serialize_by_alias=True,
    )

    count: int = pydantic.Field(
        ...,
        description="Cantidad total de usuarios.",
    )

    fromDate: typing.Optional[int] = pydantic.Field(
        default=None,
        description="Timestamp inicial (segundos Unix) utilizado en el filtrado.",
    )

    toDate: typing.Optional[int] = pydantic.Field(
        default=None,
        description="Timestamp final (segundos Unix) utilizado en el filtrado.",
    )

class UserPortalDistributionSchema(pydantic.BaseModel):

    model_config = pydantic.ConfigDict(
        extra="ignore",
        validate_by_alias=True,
        validate_by_name=True,
        serialize_by_alias=True,
    )

    portal: str = pydantic.Field(
        ...,
        description="Portal mediante el cual se registró el usuario (valor de userLevel).",
    )

    totalUsers: int = pydantic.Field(
        ...,
        description="Total de usuarios registrados en este portal.",
    )

    genreDistribution: typing.Dict[
        typing.Literal["Mujer", "Hombre"] | str, int] = pydantic.Field(
        ...,
        description="Distribución de usuarios por género.",
        examples=[
            {"Mujer": 150, "Hombre": 200},
            {"Mujer": 300, "Hombre": 400, "No Binario": 50},
        ]
    )

    ageDistribution: typing.Dict[str, int] = pydantic.Field(
        ...,
        description="Distribución de usuarios por rangos de edad (calculada con la fecha de nacimiento).",
        examples=[
            {
                "18-24": 100,
                "25-34": 150,
                "35-44": 200,
                "45-54": 250,
                "55-64": 300,
                "65+": 350
            },
        ]
    )

    fromDate: typing.Optional[int] = pydantic.Field(
        default=None,
        description="Timestamp inicial (segundos Unix) utilizado en el filtrado.",
    )


    toDate: typing.Optional[int] = pydantic.Field(
        default=None,
        description="Timestamp final (segundos Unix) utilizado en el filtrado.",
    )


class UserPortalListSchema(pydantic.BaseModel):

    model_config = pydantic.ConfigDict(
        extra="ignore",
        validate_by_alias=True,
        validate_by_name=True,
        serialize_by_alias=True,
    )

    portals: list[int] = pydantic.Field(
        default_factory=list,
        description="Listado ordenado de portales (userLevel) disponibles.",
    )