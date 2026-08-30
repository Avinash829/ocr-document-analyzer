from fastapi import APIRouter, File, HTTPException, Request, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.schemas.assessment import Assessment, GradingResult, JobResponse
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


class GradeRequest(BaseModel):
    mappingId: str | None = None
    questionId: str
    answerId: str


class ReportRequest(BaseModel):
    grades: dict


@router.post("/{assessment_id}/report")
def generate_report(request: Request, assessment_id: str, payload: ReportRequest):
    job = store(request).get(assessment_id)
    if not job or not job.result:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Assessment not found or not ready."})
    
    gemini = store(request)._gemini
    if not gemini:
        raise HTTPException(status_code=503, detail={"code": "AI_UNAVAILABLE", "message": "AI services are not configured."})
        
    performance_lines = []
    for q in job.result.questions:
        if q.id in payload.grades:
            grade_info = payload.grades[q.id]
            score = grade_info.get("score", 0)
            max_score = grade_info.get("maxScore", 0)
            feedback = grade_info.get("feedback", "")
            performance_lines.append(f"Q: {q.text} | Score: {score}/{max_score} | Feedback: {feedback}")
    
    performance_data = "\n".join(performance_lines)
    if not performance_data:
        return {"overallFeedback": "No graded answers found to generate a report."}
        
    from app.services.gemini_report import generate_overall_report
    try:
        feedback = generate_overall_report(gemini, performance_data)
        return {"overallFeedback": feedback}
    except Exception as exc:
        raise HTTPException(status_code=500, detail={"code": "REPORT_FAILED", "message": str(exc)})



@router.post("/{assessment_id}/grade", response_model=GradingResult)
def grade_answer(request: Request, assessment_id: str, payload: GradeRequest):
    job = store(request).get(assessment_id)
    if not job or not job.result:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Assessment not found or not ready."})
    
    question = next((q for q in job.result.questions if q.id == payload.questionId), None)
    answer = next((a for a in job.result.answers if a.id == payload.answerId), None)
    
    if not question or not answer:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Question or answer not found in this assessment."})
    
    gemini = store(request)._gemini
    if not gemini:
        raise HTTPException(status_code=503, detail={"code": "AI_UNAVAILABLE", "message": "AI services are not configured."})
        
    from app.services.gemini_grader import grade_answer_with_gemini
    
    try:
        result = grade_answer_with_gemini(gemini, question, answer)
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail={"code": "GRADING_FAILED", "message": str(exc)})

