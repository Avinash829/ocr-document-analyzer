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
    question_id: str = Field(
        description="The exact 'id' or label of the question being mapped (e.g. 'q_12345' or '1')."
    )
    answer_id: str | None = Field(
        default=None,
        description="The exact 'id' of the matched answer (e.g. 'a_67890'), or null if unanswered."
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
You are an expert educational grading system. Your task is to map extracted student answers to the correct printed questions.

**Questions from Question Paper:**
{questions_block}

**Extracted Answers from Answer Sheet:**
{answers_block}

**Rules:**
1. Examine each question and find the student answer that best corresponds to it.
2. Primary matching: Use student label / rawLabel first (e.g., Student Label "Q1" or "1" maps to Question Label "1" or "Q1").
3. Semantic matching: If labels are missing ("No Label"), incorrect, or ambiguous, compare the text of the student answer to the text of the question to find the true semantic match.
4. Each answer can only be matched to ONE question. Don't reuse answers across multiple questions.
5. If a question has no matching answer at all, set status to "UNANSWERED" and answer_id to null.
6. Set confidence based on how certain you are about the match.
7. Return one mapping entry for EVERY question listed above, using its exact question `id`.

Return ONLY valid JSON matching the schema.
"""


def _build_questions_block(questions: list[Question]) -> str:
    lines: list[str] = []
    for q in sorted(questions, key=lambda q: q.order):
        text_preview = q.text[:300].replace("\n", " ")
        lines.append(f"  Question id='{q.id}' [Label: Q{q.displayNumber}]: {text_preview}")
    return "\n".join(lines)


def _build_answers_block(answers: list[Answer]) -> str:
    lines: list[str] = []
    for a in answers:
        label = a.rawLabel or "No Label"
        text_preview = a.text[:300].replace("\n", " ")
        pages = ", ".join(str(p) for p in a.pages)
        lines.append(f"  Answer id='{a.id}' [Student Label: {label}] [Page {pages}]: {text_preview}")
    return "\n".join(lines)


# ── Public API ───────────────────────────────────────────────────────────

def map_answers_with_gemini(
    gemini: GeminiService,
    questions: list[Question],
    answers: list[Answer],
) -> list[Mapping]:
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

    # Build multi-index question lookup
    question_lookup: dict[str, Question] = {}
    for q in questions:
        question_lookup[q.id] = q
        question_lookup[q.displayNumber] = q
        question_lookup[q.normalizedNumber] = q
        norm = normalize_question_number(q.displayNumber)
        if norm:
            question_lookup[norm] = q
        clean_disp = q.displayNumber.lstrip("Qq").strip(". ")
        if clean_disp:
            question_lookup[clean_disp] = q
            question_lookup[f"Q{clean_disp}"] = q

    answer_map = {a.id: a for a in answers}
    used_answer_ids: set[str] = set()
    result: list[Mapping] = []

    for item in response.mappings:
        q_identifier = item.question_id.strip()
        question = question_lookup.get(q_identifier)
        if not question:
            norm_id = normalize_question_number(q_identifier)
            if norm_id:
                question = question_lookup.get(norm_id)
        if not question:
            clean_q = q_identifier.lstrip("Qq").strip(". ")
            question = question_lookup.get(clean_q)

        if not question:
            logger.warning(f"Could not resolve mapped question: {q_identifier}")
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

    # Handle any questions missed in Gemini response
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

    # Deterministic Fallback: For any unanswered question, check if there is an unused answer with matching label
    for m in result:
        if m.status == MappingStatus.UNANSWERED:
            question = next((q for q in questions if q.id == m.questionId), None)
            if not question:
                continue

            matching_answer = None
            q_norm = question.normalizedNumber or normalize_question_number(question.displayNumber)
            q_disp = question.displayNumber.lstrip("Qq").strip(". ")

            for a in answers:
                if a.id in used_answer_ids:
                    continue
                a_label = (a.rawLabel or "").strip()
                a_norm = a.normalizedLabel or normalize_question_number(a_label)
                a_clean = a_label.lstrip("Qq").strip(". ")

                if (q_norm and a_norm and q_norm == a_norm) or (q_disp and a_clean and q_disp == a_clean):
                    matching_answer = a
                    break

            if matching_answer:
                matching_answer.status = AnswerStatus.MATCHED
                used_answer_ids.add(matching_answer.id)
                m.answerId = matching_answer.id
                m.status = MappingStatus.ANSWERED
                m.confidence = 0.95
                m.method = MappingMethod.EXPLICIT_LABEL
                m.evidence = [f"Deterministic label match: {matching_answer.rawLabel} -> Q{question.displayNumber}"]
                m.regions = matching_answer.regions

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
