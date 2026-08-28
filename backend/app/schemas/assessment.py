from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, Field, model_validator


Confidence = Annotated[float, Field(ge=0, le=1)]


class JobStage(StrEnum):
    UPLOADING = "UPLOADING"
    VALIDATING = "VALIDATING"
    READING_QUESTION_PAPER = "READING_QUESTION_PAPER"
    EXTRACTING_QUESTIONS = "EXTRACTING_QUESTIONS"
    READING_ANSWER_SHEET = "READING_ANSWER_SHEET"
    EXTRACTING_ANSWERS = "EXTRACTING_ANSWERS"
    MAPPING_ANSWERS = "MAPPING_ANSWERS"
    VALIDATING_RESULTS = "VALIDATING_RESULTS"
    FINALIZING = "FINALIZING"
    COMPLETED = "COMPLETED"
    ERROR = "ERROR"
    DEGRADED = "DEGRADED"


class MappingStatus(StrEnum):
    ANSWERED = "ANSWERED"
    UNANSWERED = "UNANSWERED"
    AMBIGUOUS = "AMBIGUOUS"


class AnswerStatus(StrEnum):
    MATCHED = "MATCHED"
    UNMATCHED = "UNMATCHED"


class MappingMethod(StrEnum):
    EXPLICIT_LABEL = "EXPLICIT_LABEL"
    NORMALIZED_LABEL = "NORMALIZED_LABEL"
    SPATIAL_MATCH = "SPATIAL_MATCH"
    CONTINUATION = "CONTINUATION"
    SEMANTIC_MATCH = "SEMANTIC_MATCH"
    AI_DISAMBIGUATION = "AI_DISAMBIGUATION"
    AI_VISION = "AI_VISION"
    AMBIGUOUS = "AMBIGUOUS"
    NONE = "NONE"


class BoundingBox(BaseModel):
    x: float = Field(ge=0)
    y: float = Field(ge=0)
    width: float = Field(gt=0)
    height: float = Field(gt=0)


class Region(BaseModel):
    page: int = Field(ge=1)
    bbox: BoundingBox
    pageWidth: float = Field(gt=0)
    pageHeight: float = Field(gt=0)

    @model_validator(mode="after")
    def within_page(self):
        tolerance = 1.0
        if self.bbox.x + self.bbox.width > self.pageWidth + tolerance:
            raise ValueError("region exceeds page width")
        if self.bbox.y + self.bbox.height > self.pageHeight + tolerance:
            raise ValueError("region exceeds page height")
        return self


class DocumentPage(BaseModel):
    page: int = Field(ge=1)
    width: float = Field(gt=0)
    height: float = Field(gt=0)
    imageUrl: str


class DocumentInfo(BaseModel):
    filename: str
    pageCount: int = Field(ge=1)
    pages: list[DocumentPage]


class Question(BaseModel):
    id: str
    displayNumber: str
    normalizedNumber: str
    text: str
    page: int = Field(ge=1)
    bbox: BoundingBox | None = None
    pageWidth: float | None = None
    pageHeight: float | None = None
    order: int = Field(ge=0)
    parentId: str | None = None
    marks: float | None = Field(default=None, ge=0)
    confidence: Confidence = 1.0


class VisualElement(BaseModel):
    type: str
    description: str


class Answer(BaseModel):
    id: str
    rawLabel: str | None = None
    normalizedLabel: str | None = None
    text: str
    visualElements: list[VisualElement] = []
    regions: list[Region]
    pages: list[int]
    confidence: Confidence
    status: AnswerStatus = AnswerStatus.UNMATCHED
    evidence: list[str] = []


class Mapping(BaseModel):
    questionId: str
    answerId: str | None
    status: MappingStatus
    confidence: Confidence
    method: MappingMethod
    evidence: list[str]
    regions: list[Region]

    @model_validator(mode="after")
    def coherent_state(self):
        if self.status == MappingStatus.UNANSWERED and (self.answerId or self.regions):
            raise ValueError("unanswered mappings cannot contain an answer or regions")
        if self.status == MappingStatus.ANSWERED and not self.answerId:
            raise ValueError("answered mappings require an answer")
        return self


class ProcessingState(BaseModel):
    stage: JobStage
    progress: int | None = Field(default=None, ge=0, le=100)
    message: str
    degradedReasons: list[str] = []


class GradingResult(BaseModel):
    score: float
    maxScore: float
    isCorrect: bool
    strengths: list[str]
    advice: list[str]
    feedback: str


class AssessmentSummary(BaseModel):
    totalQuestions: int
    answered: int
    unanswered: int
    ambiguous: int
    unmatchedAnswers: int


class Assessment(BaseModel):
    id: str
    questionPaper: DocumentInfo
    answerSheet: DocumentInfo
    questions: list[Question]
    answers: list[Answer]
    mappings: list[Mapping]
    unmatchedAnswers: list[Answer]
    processing: ProcessingState
    summary: AssessmentSummary


class ApiError(BaseModel):
    code: str
    message: str
    stage: JobStage | None = None


class JobResponse(BaseModel):
    id: str
    processing: ProcessingState
    error: ApiError | None = None

