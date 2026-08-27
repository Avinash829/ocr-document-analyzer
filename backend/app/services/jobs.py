import logging
import shutil
import tempfile
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from threading import Lock

from app.config import Settings
from app.schemas.assessment import (
    ApiError, Assessment, AssessmentSummary, JobResponse, JobStage, ProcessingState,
)
from app.services.answer_extractor import extract_answers
from app.services.documents import render_document
from app.services.mapping import MappingConfig, map_answers
from app.services.ocr import OcrUnavailableError, PaddleOcrService
from app.services.question_extractor import extract_questions
from app.utils.files import ValidatedUpload

logger = logging.getLogger(__name__)


@dataclass
class Job:
    id: str
    root: Path
    processing: ProcessingState
    created_at: float = field(default_factory=time.monotonic)
    result: Assessment | None = None
    error: ApiError | None = None


class JobStore:
    def __init__(self, settings: Settings, ocr: PaddleOcrService | None = None):
        self.settings = settings
        self.ocr = ocr or PaddleOcrService()
        self._jobs: dict[str, Job] = {}
        self._lock = Lock()
        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="assessment")

    def create(self, question_upload: ValidatedUpload, answer_upload: ValidatedUpload) -> Job:
        self.cleanup_expired()
        identifier = uuid.uuid4().hex
        root = Path(tempfile.mkdtemp(prefix=f"assessment-{identifier[:8]}-"))
        job = Job(identifier, root, ProcessingState(stage=JobStage.VALIDATING, progress=5, message="Files validated"))
        with self._lock:
            self._jobs[identifier] = job
        self._executor.submit(self._process_safely, job, question_upload, answer_upload)
        return job

    def get(self, identifier: str) -> Job | None:
        with self._lock:
            return self._jobs.get(identifier)

    def response(self, job: Job) -> JobResponse:
        return JobResponse(id=job.id, processing=job.processing, error=job.error)

    def update(self, job: Job, stage: JobStage, progress: int, message: str):
        job.processing = ProcessingState(stage=stage, progress=progress, message=message, degradedReasons=job.processing.degradedReasons)

    def _process_safely(self, job: Job, question_upload: ValidatedUpload, answer_upload: ValidatedUpload):
        try:
            self._process(job, question_upload, answer_upload)
        except Exception:
            logger.exception("assessment_failed", extra={"assessment_id": job.id, "stage": job.processing.stage})
            job.error = ApiError(code="PROCESSING_FAILED", message="The assessment could not be processed.", stage=job.processing.stage)
            job.processing = ProcessingState(stage=JobStage.ERROR, message="Processing failed")
            shutil.rmtree(job.root, ignore_errors=True)

    def _process(self, job: Job, question_upload: ValidatedUpload, answer_upload: ValidatedUpload):
        self.update(job, JobStage.READING_QUESTION_PAPER, 10, "Rendering question paper")
        question_doc, question_assets = render_document(question_upload, job.root / "questions", f"/api/assessments/{job.id}/pages/questions")
        self.update(job, JobStage.READING_ANSWER_SHEET, 20, "Rendering answer sheet")
        answer_doc, answer_assets = render_document(answer_upload, job.root / "answers", f"/api/assessments/{job.id}/pages/answers")
        self.update(job, JobStage.EXTRACTING_QUESTIONS, 30, "Extracting printed questions")
        degraded: list[str] = []
        try:
            question_lines = [(a.page, a.width, a.height, self.ocr.analyze(a.path)) for a in question_assets]
            questions = extract_questions(question_lines)
            self.update(job, JobStage.EXTRACTING_ANSWERS, 55, "Extracting answer regions")
            answer_lines = [(a.page, a.width, a.height, self.ocr.analyze(a.path)) for a in answer_assets]
            answers = extract_answers(answer_lines)
        except OcrUnavailableError:
            questions, answers = [], []
            degraded.append("OCR_UNAVAILABLE")
        self.update(job, JobStage.MAPPING_ANSWERS, 75, "Mapping answers to questions")
        mappings = map_answers(questions, answers, MappingConfig(semantic_threshold=self.settings.ambiguous_threshold))
        self.update(job, JobStage.VALIDATING_RESULTS, 90, "Validating coordinates and result")
        unmatched = [answer for answer in answers if answer.status == "UNMATCHED"]
        summary = AssessmentSummary(
            totalQuestions=len(questions), answered=sum(m.status == "ANSWERED" for m in mappings),
            unanswered=sum(m.status == "UNANSWERED" for m in mappings),
            ambiguous=sum(m.status == "AMBIGUOUS" for m in mappings), unmatchedAnswers=len(unmatched),
        )
        final_stage = JobStage.DEGRADED if degraded else JobStage.COMPLETED
        processing = ProcessingState(stage=final_stage, progress=100, message="Assessment ready" if not degraded else "Assessment ready with limited extraction", degradedReasons=degraded)
        job.result = Assessment(
            id=job.id, questionPaper=question_doc, answerSheet=answer_doc, questions=questions,
            answers=answers, mappings=mappings, unmatchedAnswers=unmatched, processing=processing, summary=summary,
        )
        job.processing = processing

    def page_path(self, job: Job, document: str, page: int) -> Path | None:
        folder = "questions" if document == "questions" else "answers" if document == "answers" else None
        if not folder or page < 1:
            return None
        path = job.root / folder / f"page-{page}.png"
        return path if path.is_file() else None

    def cleanup_expired(self):
        cutoff = time.monotonic() - self.settings.job_ttl_seconds
        with self._lock:
            expired = [identifier for identifier, job in self._jobs.items() if job.created_at < cutoff]
            jobs = [self._jobs.pop(identifier) for identifier in expired]
        for job in jobs:
            shutil.rmtree(job.root, ignore_errors=True)

    def close(self):
        self._executor.shutdown(wait=True, cancel_futures=True)
        with self._lock:
            jobs, self._jobs = list(self._jobs.values()), {}
        for job in jobs:
            shutil.rmtree(job.root, ignore_errors=True)
