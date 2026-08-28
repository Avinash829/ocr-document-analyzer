"""Gemini AI-powered answer-to-question mapping.

Instead of using token similarity heuristics, this sends ALL extracted
questions and answers as text to Gemini and asks it to perform the
semantic matching. This handles:
- Out-of-order answers
- Missing/wrong labels
- Semantic matching when labels are absent
- Unanswered question detection
"""

import logging
import uuid

from pydantic import BaseModel, Field

from app.schemas.assessment import (
    Answer,
    AnswerStatus,
    Mapping,
    MappingMethod,
    MappingStatus,
    Question,
    Region,
)
from app.services.gemini import GeminiService, GeminiServiceError
from app.utils.normalization import normalize_question_number

logger = logging.getLogger(__name__)


# ── Pydantic models for structured Gemini response ──────────────────────

class GeminiMappingItem(BaseModel):
    """One question-to-answer mapping produced by Gemini."""
    question_number: str = Field(
        description="The question number being mapped (e.g. '1', '2', '3(a)')."
    )
    answer_id: str | None = Field(
        default=None,
        description="The ID of the matched answer, or null if the question is unanswered."
    )
    status: str = Field(
        description="One of: 'ANSWERED', 'UNANSWERED', 'AMBIGUOUS'."
    )
    confidence: float = Field(
        ge=0, le=1,
        description="Confidence in this mapping (0 = guess, 1 = certain)."
    )
    reasoning: str = Field(
        description="Brief explanation of why this mapping was chosen."
    )


class GeminiMappingResponse(BaseModel):
    """Structured response from Gemini for answer mapping."""
    mappings: list[GeminiMappingItem] = Field(
        default_factory=list,
        description="One mapping entry per question."
    )


# ── Prompt ───────────────────────────────────────────────────────────────

_PROMPT_TEMPLATE = """\
You are mapping student answers to exam questions.

**Questions:**
{questions_block}

**Extracted Answers:**
{answers_block}

**Rules:**
1. For each question, find the best matching answer from the list above.
2. Match by answer label first (e.g., answer with rawLabel "2" matches question "2").
3. If labels don't match or are missing ("No Label"), use semantic content matching — \
compare the answer text to the question text to find the best match.
4. Each answer can only be matched to ONE question. Don't reuse answers.
5. If a question has no matching answer at all, set status to "UNANSWERED" and answer_id to null.
6. If multiple answers could match a question and you're not sure, set status to "AMBIGUOUS".
7. Set confidence based on how certain you are about the match.
8. Provide brief reasoning for each mapping decision.
9. Return one mapping entry for EVERY question, even unanswered ones.

Return ONLY valid JSON matching the schema.
"""


def _build_questions_block(questions: list[Question]) -> str:
    lines: list[str] = []
    for q in sorted(questions, key=lambda q: q.order):
        text_preview = q.text[:300].replace("\n", " ")
        lines.append(f"  Q{q.normalizedNumber} (id={q.id}): {text_preview}")
    return "\n".join(lines)


def _build_answers_block(answers: list[Answer]) -> str:
    lines: list[str] = []
    for a in answers:
        label = a.rawLabel or "No Label"
        text_preview = a.text[:300].replace("\n", " ")
        pages = ", ".join(str(p) for p in a.pages)
        lines.append(f"  Answer id={a.id} [label: {label}] [pages: {pages}]: {text_preview}")
    return "\n".join(lines)


# ── Public API ───────────────────────────────────────────────────────────

def map_answers_with_gemini(
    gemini: GeminiService,
    questions: list[Question],
    answers: list[Answer],
) -> list[Mapping]:
    """Map answers to questions using Gemini's semantic understanding.

    Parameters
    ----------
    gemini : GeminiService
        Configured Gemini client.
    questions : list[Question]
        All extracted questions.
    answers : list[Answer]
        All extracted answers.

    Returns
    -------
    list[Mapping]
        One mapping per question.

    Raises
    ------
    GeminiServiceError
        When Gemini is unavailable.
    """
    if not questions:
        return []

    questions_block = _build_questions_block(questions)
    answers_block = _build_answers_block(answers) if answers else "  (No answers were extracted)"
    prompt = _PROMPT_TEMPLATE.format(
        questions_block=questions_block,
        answers_block=answers_block,
    )

    response = gemini.analyze(
        prompt=prompt,
        image_paths=[],  # Text-only, no images needed
        schema=GeminiMappingResponse,
    )

    # Build lookup maps
    question_map = {q.normalizedNumber: q for q in questions}
    answer_map = {a.id: a for a in answers}
    used_answer_ids: set[str] = set()
    result: list[Mapping] = []

    for item in response.mappings:
        normalized_number = normalize_question_number(item.question_number) or item.question_number.strip()
        question = question_map.get(normalized_number)
        if not question:
            # Try to find by display number
            question = next(
                (q for q in questions if q.displayNumber == item.question_number),
                None,
            )
        if not question:
            continue

        status_str = item.status.upper()

        if (
            status_str == "ANSWERED"
            and item.answer_id
            and item.answer_id in answer_map
            and item.answer_id not in used_answer_ids
        ):
            answer = answer_map[item.answer_id]
            answer.status = AnswerStatus.MATCHED
            used_answer_ids.add(answer.id)
            result.append(Mapping(
                questionId=question.id,
                answerId=answer.id,
                status=MappingStatus.ANSWERED,
                confidence=max(0.85, item.confidence),
                method=MappingMethod.AI_VISION,
                evidence=[f"AI mapping: {item.reasoning}"],
                regions=answer.regions,
            ))
        elif status_str == "AMBIGUOUS":
            regions = []
            if item.answer_id and item.answer_id in answer_map:
                regions = answer_map[item.answer_id].regions
            result.append(Mapping(
                questionId=question.id,
                answerId=None,
                status=MappingStatus.AMBIGUOUS,
                confidence=item.confidence,
                method=MappingMethod.AI_VISION,
                evidence=[f"AI mapping (ambiguous): {item.reasoning}"],
                regions=regions,
            ))
        else:
            evidence = (
                "AI mapping rejected because it reused an answer" if item.answer_id in used_answer_ids
                else f"AI mapping: {item.reasoning}"
            )
            result.append(Mapping(
                questionId=question.id,
                answerId=None,
                status=MappingStatus.UNANSWERED,
                confidence=item.confidence,
                method=MappingMethod.AI_VISION,
                evidence=[evidence],
                regions=[],
            ))

    # Handle any questions that Gemini missed in its response
    mapped_question_ids = {m.questionId for m in result}
    for question in questions:
        if question.id not in mapped_question_ids:
            result.append(Mapping(
                questionId=question.id,
                answerId=None,
                status=MappingStatus.UNANSWERED,
                confidence=0.5,
                method=MappingMethod.NONE,
                evidence=["Question not included in AI mapping response"],
                regions=[],
            ))

    logger.info(
        "gemini_mapping_complete",
        extra={
            "questions": len(questions),
            "answers": len(answers),
            "answered": sum(1 for m in result if m.status == MappingStatus.ANSWERED),
            "unanswered": sum(1 for m in result if m.status == MappingStatus.UNANSWERED),
        },
    )
    return result
