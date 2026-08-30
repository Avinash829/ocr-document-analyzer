import logging
from pydantic import BaseModel, Field

from app.services.gemini import GeminiService, GeminiServiceError

logger = logging.getLogger(__name__)


class GeminiReportResponse(BaseModel):
    """Structured report response from Gemini."""
    overallFeedback: str = Field(
        description="A clear, short personalized 2-sentence overall performance summary based on the provided answers."
    )


_PROMPT_TEMPLATE = """\
You are an expert, impartial academic grader. The student has just completed an assessment.
Below are the individual questions, the score they received, and the specific feedback given for each question.

**Student Performance Data:**
{performance_data}

**Instructions:**
Provide a personalized, encouraging 2-sentence overall performance summary.
Address the student directly (e.g., "Great job overall...").
Highlight their main strength and one general area for improvement based on the data.
Keep it strictly to 2 sentences.

Return ONLY valid JSON matching the schema.
"""


def generate_overall_report(
    gemini: GeminiService,
    performance_data: str,
) -> str:
    prompt = _PROMPT_TEMPLATE.format(performance_data=performance_data)

    try:
        response = gemini.analyze(
            prompt=prompt,
            image_paths=[],
            schema=GeminiReportResponse,
        )
    except GeminiServiceError:
        logger.warning("gemini_report_failed")
        raise

    return response.overallFeedback
