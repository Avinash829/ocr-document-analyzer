"""Gemini Vision-based question extraction.

Sends ALL question-paper page images to Gemini in ONE API call to extract all
questions with their exact numbering, sub-parts, marks, and bounding boxes.
This replaces the PaddleOCR + regex approach for much higher accuracy and
optimizes token usage to prevent rate limits.
"""

import logging
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from pydantic import BaseModel, Field

from app.schemas.assessment import BoundingBox, Question
from app.services.gemini import GeminiService, GeminiServiceError

logger = logging.getLogger(__name__)


# ── Pydantic models for structured Gemini response ──────────────────────

class GeminiQuestionItem(BaseModel):
    """One question extracted by Gemini from the question paper."""
    page_number: int = Field(
        description="The 1-indexed page number this question appears on (1 for the first image)."
    )
    number: str = Field(
        description="The exact printed question number, e.g. '1', '2', '3(a)', '3(b)', '4.1'. "
                    "Preserve the original numbering exactly as printed."
    )
    text: str = Field(
        description="The full text of the question, excluding headers/footers/instructions."
    )
    parent_number: str | None = Field(
        default=None,
        description="If this is a sub-part, the parent question number (e.g. '3' for '3(a)'). Otherwise null."
    )
    sub_part: str | None = Field(
        default=None,
        description="The sub-part label if applicable (e.g. 'a' for '3(a)'). Otherwise null."
    )
    marks: float | None = Field(
        default=None, ge=0,
        description="Marks allocated to this question if visible (e.g. 5.0). Otherwise null."
    )
    confidence: float = Field(
        ge=0, le=1,
        description="Your confidence in the extraction accuracy (0 = guess, 1 = certain)."
    )
    bbox_x: int = Field(
        ge=0, le=1000,
        description="Left edge of the question region, normalized 0-1000 (0=left, 1000=right)."
    )
    bbox_y: int = Field(
        ge=0, le=1000,
        description="Top edge of the question region, normalized 0-1000 (0=top, 1000=bottom)."
    )
    bbox_w: int = Field(
        ge=0, le=1000,
        description="Width of the question region, normalized 0-1000."
    )
    bbox_h: int = Field(
        ge=0, le=1000,
        description="Height of the question region, normalized 0-1000."
    )


class GeminiQuestionResponse(BaseModel):
    """Structured response from Gemini for the entire question paper."""
    questions: list[GeminiQuestionItem] = Field(
        default_factory=list,
        description="List of all questions found across all pages."
    )


# ── Prompt ───────────────────────────────────────────────────────────────

_PROMPT = """\
You are an expert academic OCR agent. Your task is to extract every exam question \
from the provided question paper images. You will receive multiple images representing \
the consecutive pages of the question paper.

Follow these strict rules:
1. Preserve the exact printed question numbering (e.g., "1", "2(a)", "3.1"). Do NOT renumber.
2. Identify sub-parts (e.g. a, b, c) and extract them as individual question entries. \
Set "parent_number" to the main question number (e.g. "3" for "3(a)") and "sub_part" \
to the sub-part letter (e.g. "a").
3. Do NOT include exam headers, instructions, page numbers, footers, or mark schemes as questions.
4. Extract the full text of each question accurately.
5. If marks are shown next to the question (e.g. "[5 marks]", "(3)"), extract them in the "marks" field.
6. Provide a normalized bounding box for each question relative to the page it is on, \
using coordinates from 0 to 1000, where (0,0) is top-left and (1000,1000) is bottom-right.
7. Set the "page_number" correctly. The first image provided is page 1, the second is page 2, etc.
8. If uncertain about a question's text, still extract it but output a lower confidence.

Return ONLY valid JSON matching the schema.
"""


# ── Public API ───────────────────────────────────────────────────────────

def extract_questions_with_gemini(
    gemini: GeminiService,
    page_images: list[tuple[int, Path, int, int]],
) -> list[Question]:
    """Extract questions with one bounded Gemini Vision request per page.

    Parameters
    ----------
    gemini : GeminiService
        Configured Gemini client with key pool.
    page_images : list[tuple[int, Path, int, int]]
        Each entry is ``(page_number, image_path, page_width, page_height)``.

    Returns
    -------
    list[Question]
        Question objects in printed order.

    Raises
    ------
    GeminiServiceError
        When all Gemini keys are exhausted or the request fails.
    """
    if not page_images:
        return []

    def extract_page(page_image: tuple[int, Path, int, int]) -> tuple[tuple[int, Path, int, int], GeminiQuestionResponse]:
        page_number, image_path, _width, _height = page_image
        response = gemini.analyze(
            prompt=f"{_PROMPT}\nThis is page {page_number} of the question paper. Return only questions visible on this page.",
            image_paths=[image_path],
            schema=GeminiQuestionResponse,
        )
        return page_image, response

    page_results: list[tuple[tuple[int, Path, int, int], GeminiQuestionResponse]] = []
    errors: list[GeminiServiceError] = []
    with ThreadPoolExecutor(max_workers=min(2, len(page_images)), thread_name_prefix="gemini-question") as executor:
        futures = [executor.submit(extract_page, page_image) for page_image in page_images]
        for future in as_completed(futures):
            try:
                page_results.append(future.result())
            except GeminiServiceError as exc:
                errors.append(exc)
                logger.warning("gemini_question_page_failed", extra={"error": str(exc)})

    if not page_results:
        raise errors[0] if errors else GeminiServiceError("RETRYABLE_TRANSIENT", "No question pages could be processed.")

    all_questions: list[Question] = []
    for (original_page_num, _image_path, page_width, page_height), response in sorted(page_results, key=lambda item: item[0][0]):
        for item in response.questions:
            # Convert 0-1000 normalized coords to pixel coords.
            bbox = BoundingBox(
                x=max(0, (item.bbox_x / 1000) * page_width),
                y=max(0, (item.bbox_y / 1000) * page_height),
                width=max(1, (item.bbox_w / 1000) * page_width),
                height=max(1, (item.bbox_h / 1000) * page_height),
            )
            if bbox.x + bbox.width > page_width:
                bbox.width = max(1, page_width - bbox.x)
            if bbox.y + bbox.height > page_height:
                bbox.height = max(1, page_height - bbox.y)
            normalized = item.number.strip()

            all_questions.append(Question(
                id=f"q_{uuid.uuid4().hex[:12]}",
                displayNumber=item.number,
                normalizedNumber=normalized,
                text=item.text.strip(),
                page=original_page_num,
                bbox=bbox,
                pageWidth=page_width,
                pageHeight=page_height,
                order=len(all_questions),
                parentId=item.parent_number,
                marks=item.marks,
                confidence=item.confidence,
            ))

    logger.info(
        "gemini_question_extraction_complete",
        extra={"pages": len(page_images), "pages_failed": len(errors), "questions_found": len(all_questions)},
    )
    return all_questions
