"""Gemini Vision-based answer extraction.

Sends ALL answer-sheet page images along with the full list of questions
to Gemini in **ONE API call**.  Gemini returns structured JSON
with the extracted answer text, visual elements, and normalised bounding-box
coordinates (0-1000 system) for every answer it can locate across all pages.

When Gemini is unavailable the caller should fall back to the
PaddleOCR + heuristic pipeline.
"""

import logging
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from pydantic import BaseModel, Field

from app.schemas.assessment import (
    Answer,
    AnswerStatus,
    BoundingBox,
    Question,
    Region,
    VisualElement,
)
from app.services.gemini import GeminiService, GeminiServiceError

logger = logging.getLogger(__name__)


# ── Pydantic models for structured Gemini response ──────────────────────

class GeminiVisualElement(BaseModel):
    """A visual element (diagram, equation, table, etc.) within an answer."""
    type: str = Field(
        description="The visual type: diagram, drawing, equation, graph, table, flowchart, symbol, annotation, or other"
    )
    description: str = Field(
        description="Detailed text description of what this visual element depicts"
    )


class GeminiAnswerItem(BaseModel):
    """One answer block identified by Gemini."""
    page_number: int = Field(
        description="The 1-indexed page number this answer appears on (1 for the first image)."
    )
    raw_question_reference: str = Field(
        description="The exact label the student wrote to identify this answer, "
                    "e.g. '1', 'Q1', 'Ans 2(a)', '3.', 'No Label' if no label is visible."
    )
    question_number: str = Field(
        description="The normalised question number this answer belongs to, e.g. '1', '2', '3(a)'. "
                    "Use just the number, no prefix like 'Q' or 'Ans'. "
                    "If unlabelled, infer from content or set to 'unknown'."
    )
    answer_text: str = Field(
        description="The full transcription of the student's handwritten answer. "
                    "Include all text, formulas, and annotations."
    )
    visual_elements: list[GeminiVisualElement] = Field(
        default_factory=list,
        description="List of visual elements (diagrams, equations, tables, drawings) "
                    "found within this answer region."
    )
    bbox_x: int = Field(
        ge=0, le=1000,
        description="Left edge of the answer region, normalized 0-1000 (0=left, 1000=right)."
    )
    bbox_y: int = Field(
        ge=0, le=1000,
        description="Top edge of the answer region, normalized 0-1000 (0=top, 1000=bottom)."
    )
    bbox_w: int = Field(
        ge=0, le=1000,
        description="Width of the answer region, normalized 0-1000."
    )
    bbox_h: int = Field(
        ge=0, le=1000,
        description="Height of the answer region, normalized 0-1000."
    )
    confidence: float = Field(
        ge=0, le=1,
        description="Your confidence that this answer text and region are correct (0 = guess, 1 = certain)."
    )


class GeminiAnswerResponse(BaseModel):
    """Structured response from Gemini for the entire answer sheet."""
    answers: list[GeminiAnswerItem] = Field(
        default_factory=list,
        description="List of all answers found across all pages. Return an empty list if no answers are visible."
    )


# ── Prompt ───────────────────────────────────────────────────────────────

_PROMPT_TEMPLATE = """\
You are analyzing a student's handwritten answer sheet.
You will receive multiple images representing consecutive pages of the answer sheet.
Do NOT perform text-only OCR. Inspect the entire visual content of all pages.

Below is the list of questions the student was expected to answer:

{questions_block}

**Identify and transcribe:**
1. Handwritten text paragraphs and annotations.
2. Printed text if present.
3. Mathematical formulas and chemical equations (e.g., "6CO2 + 6H2O -> C6H12O6 + 6O2").
4. Diagrams, drawings, figures, flowcharts, graphs, charts, tables, shapes, lines, arrows, \
annotations, and labels.

**Rules:**
1. Locate every block of handwritten content, drawing, or diagram across all pages.
2. Identify the question reference written by the student (e.g. "1", "Q1", "Ans 2(a)"). \
Set this as "raw_question_reference". If no label is visible, set it to "No Label".
3. A diagram is part of the answer even if it contains little or no text. Do NOT ignore drawings.
4. Set the bounding box coordinates to capture the COMPLETE boundary of the answer region \
(encompassing both text and non-text visual elements).
5. Use normalized coordinates from 0 to 1000 relative to the specific page the answer is on, \
where (0,0) is top-left and (1000,1000) is bottom-right.
6. For each visual element (diagram, drawing, equation, table, graph), list it in "visual_elements" \
with its type and a text description.
7. Set the "page_number" correctly. The first image provided is page 1, the second is page 2, etc.
8. If an answer spans multiple pages, extract each page's part as a SEPARATE entry, but use the \
same "question_number".
9. Do NOT include page headers (roll number, date, page number) as part of any answer.
10. The "question_number" should be the normalized number (e.g. "1", "2", "3(a)") that best matches \
one of the questions listed above.

Return ONLY valid JSON matching the schema.
"""


def _build_questions_block(questions: list[Question]) -> str:
    lines: list[str] = []
    for q in sorted(questions, key=lambda q: q.order):
        text_preview = q.text[:300].replace("\n", " ")
        lines.append(f"  Q{q.normalizedNumber}: {text_preview}")
    return "\n".join(lines)


# ── Public API ───────────────────────────────────────────────────────────

def extract_answers_with_gemini(
    gemini: GeminiService,
    questions: list[Question],
    page_images: list[tuple[int, Path, int, int]],
) -> list[Answer]:
    """Extract answers with one bounded Gemini Vision request per page.

    Parameters
    ----------
    gemini : GeminiService
        Configured Gemini client with key pool.
    questions : list[Question]
        All questions extracted from the question paper.
    page_images : list[tuple[int, Path, int, int]]
        Each entry is ``(page_number, image_path, page_width, page_height)``.

    Returns
    -------
    list[Answer]
        Answer objects ready for the mapping stage.

    Raises
    ------
    GeminiServiceError
        When all Gemini keys are exhausted or the request fails.
    """
    if not questions or not page_images:
        return []

    references = ", ".join(f"Q{question.normalizedNumber}" for question in questions)
    prompt = _PROMPT_TEMPLATE.format(questions_block=f"Valid question references: {references}")

    def extract_page(page_image: tuple[int, Path, int, int]) -> tuple[tuple[int, Path, int, int], GeminiAnswerResponse]:
        page_number, image_path, _width, _height = page_image
        response = gemini.analyze(
            prompt=f"{prompt}\nThis is answer-sheet page {page_number}. Return only answer regions visible on this page.",
            image_paths=[image_path],
            schema=GeminiAnswerResponse,
        )
        return page_image, response

    page_results: list[tuple[tuple[int, Path, int, int], GeminiAnswerResponse]] = []
    errors: list[GeminiServiceError] = []
    with ThreadPoolExecutor(max_workers=min(2, len(page_images)), thread_name_prefix="gemini-answer") as executor:
        futures = [executor.submit(extract_page, page_image) for page_image in page_images]
        for future in as_completed(futures):
            try:
                page_results.append(future.result())
            except GeminiServiceError as exc:
                errors.append(exc)
                logger.warning("gemini_answer_page_failed", extra={"error": str(exc)})

    if not page_results:
        raise errors[0] if errors else GeminiServiceError("RETRYABLE_TRANSIENT", "No answer pages could be processed.")

    all_answers: list[Answer] = []

    for (original_page_num, _image_path, page_width, page_height), response in sorted(page_results, key=lambda item: item[0][0]):
      for item in response.answers:
        # Skip unknown/unlabelled if we can't match
        q_num = item.question_number.strip()
        if q_num.lower() == "unknown":
            q_num = None

        # Each request contains exactly one page, so its local page number is
        # intentionally ignored: the source asset is the coordinate authority.
        bbox = BoundingBox(
            x=max(0, (item.bbox_x / 1000) * page_width),
            y=max(0, (item.bbox_y / 1000) * page_height),
            width=max(1, (item.bbox_w / 1000) * page_width),
            height=max(1, (item.bbox_h / 1000) * page_height),
        )

        # Clamp to page bounds
        if bbox.x + bbox.width > page_width:
            bbox.width = max(1, page_width - bbox.x)
        if bbox.y + bbox.height > page_height:
            bbox.height = max(1, page_height - bbox.y)

        region = Region(
            page=original_page_num,
            bbox=bbox,
            pageWidth=page_width,
            pageHeight=page_height,
        )

        # Build evidence text
        evidence_parts = [f"Gemini Vision identified answer for Q{q_num or 'unknown'}"]
        if item.visual_elements:
            ve_summary = ", ".join(f"{ve.type}: {ve.description[:80]}" for ve in item.visual_elements)
            evidence_parts.append(f"Visual elements: {ve_summary}")

        all_answers.append(Answer(
            id=f"a_{uuid.uuid4().hex[:12]}",
            rawLabel=item.raw_question_reference,
            normalizedLabel=q_num,
            text=item.answer_text.strip(),
            visualElements=[VisualElement(type=ve.type, description=ve.description) for ve in item.visual_elements],
            regions=[region],
            pages=[original_page_num],
            confidence=item.confidence,
            status=AnswerStatus.UNMATCHED,
            evidence=evidence_parts,
        ))

    # A repeated explicit reference on a later page is a continuation.  Keep a
    # single answer identity with every page-region so the viewer can navigate it.
    merged: dict[str, Answer] = {}
    unlabelled: list[Answer] = []
    for answer in all_answers:
        if not answer.normalizedLabel:
            unlabelled.append(answer)
            continue
        previous = merged.get(answer.normalizedLabel)
        if previous is None:
            merged[answer.normalizedLabel] = answer
            continue
        if answer.pages[0] not in previous.pages:
            previous.text = "\n".join(part for part in [previous.text, answer.text] if part)
            previous.regions.extend(answer.regions)
            previous.pages.extend(answer.pages)
            previous.confidence = min(previous.confidence, answer.confidence)
            previous.evidence.append("Gemini Vision detected a continuation on a later page")
        else:
            unlabelled.append(answer)
    all_answers = [*merged.values(), *unlabelled]

    logger.info(
        "gemini_answer_extraction_complete",
        extra={"pages": len(page_images), "pages_failed": len(errors), "answers_found": len(all_answers)},
    )
    return all_answers
