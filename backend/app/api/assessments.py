from fastapi import APIRouter, File, HTTPException, Request, UploadFile, status
from fastapi.responses import FileResponse

from app.schemas.assessment import Assessment, JobResponse
from app.services.jobs import JobStore
from app.utils.files import FileValidationError, validate_upload

router = APIRouter(prefix="/api/assessments", tags=["assessments"])


def store(request: Request) -> JobStore:
    return request.app.state.jobs


@router.post("", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_assessment(request: Request, question_paper: UploadFile = File(...), answer_sheet: UploadFile = File(...)):
    settings = request.app.state.settings
    try:
        question = validate_upload(question_paper.filename, question_paper.content_type, await question_paper.read(settings.max_file_size_mb * 1024 * 1024 + 1), settings)
        answer = validate_upload(answer_sheet.filename, answer_sheet.content_type, await answer_sheet.read(settings.max_file_size_mb * 1024 * 1024 + 1), settings)
    except FileValidationError as exc:
        raise HTTPException(status_code=422, detail={"code": exc.code, "message": str(exc)}) from exc
    job = store(request).create(question, answer)
    return store(request).response(job)


@router.get("/{assessment_id}", response_model=JobResponse)
def get_assessment_job(request: Request, assessment_id: str):
    job = store(request).get(assessment_id)
    if not job:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Assessment not found or expired."})
    return store(request).response(job)


@router.get("/{assessment_id}/result", response_model=Assessment)
def get_assessment_result(request: Request, assessment_id: str):
    job = store(request).get(assessment_id)
    if not job:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Assessment not found or expired."})
    if not job.result:
        raise HTTPException(status_code=409, detail={"code": "NOT_READY", "message": "Assessment processing is not complete."})
    return job.result


@router.get("/{assessment_id}/pages/{document}/{page}", response_class=FileResponse)
def get_page(request: Request, assessment_id: str, document: str, page: int):
    job = store(request).get(assessment_id)
    path = store(request).page_path(job, document, page) if job else None
    if not path:
        raise HTTPException(status_code=404, detail={"code": "PAGE_NOT_FOUND", "message": "Document page not found."})
    return FileResponse(path, media_type="image/png", headers={"Cache-Control": "private, max-age=300"})

