"""Gemini Vision-based grading.

Grades a student's answer based on the question text, max marks, and extracted student answer.
"""

import logging
from pydantic import BaseModel, Field

from app.schemas.assessment import GradingResult, Question, Answer
from app.services.gemini import GeminiService, GeminiServiceError

logger = logging.getLogger(__name__)


# ── Pydantic models for structured Gemini response ──────────────────────

class GeminiGradingResponse(BaseModel):
    """Structured grading response from Gemini."""
    score: float = Field(
        description="The score awarded to the student for this answer, bounded between 0 and maxScore."
    )
    isCorrect: bool = Field(
        description="True if the answer is mostly or fully correct. False if it is fundamentally wrong."
    )
    strengths: list[str] = Field(
        default_factory=list,
        description="List of positive aspects or correct parts of the answer."
    )
    advice: list[str] = Field(
        default_factory=list,
        description="List of actionable advice or missing concepts the student should review."
    )
    feedback: str = Field(
        description="A clear, short overall feedback summary directed at the student."
    )


# ── Prompt ───────────────────────────────────────────────────────────────

_PROMPT_TEMPLATE = """\
You are an expert, impartial academic grader. Evaluate the student's answer \
against the provided question.

**Question Details:**
Number: {question_number}
Text: {question_text}
Max Marks: {max_marks}

**Student's Extracted Answer:**
{answer_text}

**Visual Elements Found in Answer:**
{visual_elements_text}

**Instructions:**
1. Evaluate the correctness of the student's answer.
2. Determine a fair score based on the max marks provided. Do not exceed max marks. If max marks is 0, give a score of 0.
3. List 1-3 specific strengths of their answer.
4. List 1-3 specific areas of improvement or missing concepts (advice).
5. Provide a constructive, encouraging overall feedback paragraph.
6. Set isCorrect to true if the answer demonstrates sufficient understanding, even if minor details are missing.

Return ONLY valid JSON matching the schema.
"""


def _build_visual_elements_text(answer: Answer) -> str:
    if not answer.visualElements:
        return "None"
    return "\n".join(f"- [{ve.type}] {ve.description}" for ve in answer.visualElements)


# ── Public API ───────────────────────────────────────────────────────────

def grade_answer_with_gemini(
    gemini: GeminiService,
    question: Question,
    answer: Answer,
) -> GradingResult:
    """Grades a student's answer using Gemini.

    Parameters
    ----------
    gemini : GeminiService
        Configured Gemini client with key pool.
    question : Question
        The question being answered.
    answer : Answer
        The student's answer.

    Returns
    -------
    GradingResult
        The grading results.

    Raises
    ------
    GeminiServiceError
        When all Gemini keys are exhausted or the request fails.
    """
    max_marks = float(question.marks) if question.marks is not None else 1.0
    
    prompt = _PROMPT_TEMPLATE.format(
        question_number=question.displayNumber,
        question_text=question.text,
        max_marks=max_marks,
        answer_text=answer.text or "(No text extracted)",
        visual_elements_text=_build_visual_elements_text(answer)
    )

    try:
        response = gemini.analyze(
            prompt=prompt,
            image_paths=[],  # No images sent for grading, we rely on the extracted text and visual element descriptions
            schema=GeminiGradingResponse,
        )
    except GeminiServiceError:
        logger.warning("gemini_grading_failed", extra={"question_id": question.id})
        raise

    return GradingResult(
        score=min(max(0.0, float(response.score)), max_marks),
        maxScore=max_marks,
        isCorrect=response.isCorrect,
        strengths=response.strengths,
        advice=response.advice,
        feedback=response.feedback,
    )
