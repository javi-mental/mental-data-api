import pydantic
import pydantic_mongo
import typing


class MongoDateSchema(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(
        extra="ignore",
        validate_by_alias=True,
        validate_by_name=True,
        serialize_by_alias=True,
    )

    date: str = pydantic.Field(..., alias="$date")


class AudioMotiveSchema(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(
        extra="ignore",
        validate_by_alias=True,
        validate_by_name=True,
        serialize_by_alias=True,
    )

    voice: str
    export: str
    frontAnalysis: str
    fullAnalysis: str


class QuestionSchema(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(
        extra="ignore",
        validate_by_alias=True,
        validate_by_name=True,
        serialize_by_alias=True,
    )

    question: str
    answer: str


class TextHistorySchema(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(
        extra="ignore",
        validate_by_alias=True,
        validate_by_name=True,
        serialize_by_alias=True,
    )

    text: str
    transcription: str


class AudioItemSchema(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(
        extra="ignore",
        validate_by_alias=True,
        validate_by_name=True,
        serialize_by_alias=True,
    )

    audioId: int = pydantic.Field(..., alias="audioID")
    format: str
    path: str
    text: str
    textHistorial: typing.List[TextHistorySchema] = pydantic.Field(
        default_factory=list
    )
    static: bool
    transcription: typing.Optional[str] = None
    completed: bool


class GeneratedSectionSchema(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(
        extra="ignore",
        validate_by_alias=True,
        validate_by_name=True,
        serialize_by_alias=True,
    )

    sectionId: int = pydantic.Field(..., alias="sectionID")
    questions: typing.List[QuestionSchema]
    texts: typing.List[str]
    path: str
    audios: typing.List[AudioItemSchema]
    completed: bool


class UserDataSchema(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(
        extra="ignore",
        validate_by_alias=True,
        validate_by_name=True,
        serialize_by_alias=True,
    )

    id: str = pydantic.Field(..., alias="_id")
    email: str
    names: str
    lastnames: str
    wantToBeCalled: str
    gender: str
    birthdate: str


class ExportStepDataSchema(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(
        extra="ignore",
        validate_by_alias=True,
        validate_by_name=True,
        serialize_by_alias=True,
    )

    zipFilePath: str


class DecoratorStepDataSchema(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(
        extra="ignore",
        validate_by_alias=True,
        validate_by_name=True,
        serialize_by_alias=True,
    )

    audioFilePathNoCDN: str
    audioFilePathCDN: str
    duration: str


class StepDataSchema(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(
        extra="ignore",
        validate_by_alias=True,
        validate_by_name=True,
        serialize_by_alias=True,
    )

    exportStepData: typing.Optional[ExportStepDataSchema] = None
    decoratorStepData: typing.Optional[DecoratorStepDataSchema] = None


class AudioRequestSchema(pydantic.BaseModel):
    """
    Schema para la solicitud de audios de hipnosis.
    """

    model_config = pydantic.ConfigDict(
        extra="ignore",
        validate_by_alias=True,
        validate_by_name=True,
        serialize_by_alias=True,
    )

    id: pydantic_mongo.ObjectIdAnnotation = pydantic.Field(..., alias="_id")
    userId: str
    email: str
    requestDate: str
    membershipDate: str
    status: str
    audioMotive: AudioMotiveSchema
    postHypnosis: str
    questions: typing.List[QuestionSchema]
    generatedSections: typing.List[GeneratedSectionSchema]
    generatedText: typing.List[str]
    userLevel: str
    userData: UserDataSchema
    version: str
    publicationDate: str
    errorStatus: typing.List[typing.Any]
    createdAt: MongoDateSchema
    updatedAt: MongoDateSchema
    stepData: typing.Optional[StepDataSchema] = None
    isAvailable: bool = pydantic.Field(
        default=True,
        description="Indica si el audio está disponible para escuchar (aparece como un icono en la app). True significa que aun no se ha escuchado (el icono es visible), False que ya se ha escuchado. (Desaparece el icono).",
    )

class AudioRequestCountSchema(pydantic.BaseModel):
    """
    Schema para el conteo de solicitudes de audios de hipnosis.
    """

    model_config = pydantic.ConfigDict(
        extra="ignore",
        validate_by_alias=True,
        validate_by_name=True,
        serialize_by_alias=True,
    )

    count: int = pydantic.Field(
        ...,
        description="El número total de solicitudes de audios de hipnosis.",
    )

    fromDate: typing.Optional[int] = pydantic.Field(
        default=None,
        description="Timestamp inicial (segundos Unix) utilizado para el filtrado.",
    )


    toDate: typing.Optional[int] = pydantic.Field(
        default=None,
        description="Timestamp final (segundos Unix) utilizado para el filtrado.",
    )