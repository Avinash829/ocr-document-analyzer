from dataclasses import dataclass
from difflib import SequenceMatcher

from app.schemas.assessment import (
    Answer, AnswerStatus, Mapping, MappingMethod, MappingStatus, Question,
)


@dataclass(frozen=True)
class MappingConfig:
    semantic_threshold: float = 0.68
    ambiguity_margin: float = 0.10


def _token_similarity(question: str, answer: str) -> float:
    q = " ".join(question.lower().split())
    a = " ".join(answer.lower().split())
    if not q or not a:
        return 0.0
    q_tokens, a_tokens = set(q.split()), set(a.split())
    overlap = len(q_tokens & a_tokens) / max(len(q_tokens), 1)
    sequence = SequenceMatcher(None, q, a).ratio()
    return min(1.0, 0.7 * overlap + 0.3 * sequence)


def _is_gemini_answer(answer: Answer) -> bool:
    """Check if this answer was produced by Gemini Vision."""
    return any("Gemini Vision" in e for e in answer.evidence)


def map_answers(questions: list[Question], answers: list[Answer], config: MappingConfig | None = None) -> list[Mapping]:
    config = config or MappingConfig()
    available = {answer.id: answer for answer in answers}
    result: list[Mapping] = []

    for question in sorted(questions, key=lambda item: item.order):
        exact = [a for a in available.values() if a.normalizedLabel == question.normalizedNumber]
        if len(exact) == 1:
            answer = exact[0]
            answer.status = AnswerStatus.MATCHED
            available.pop(answer.id)
            # Use AI_VISION method if answer came from Gemini
            method = MappingMethod.AI_VISION if _is_gemini_answer(answer) else MappingMethod.EXPLICIT_LABEL
            result.append(Mapping(
                questionId=question.id, answerId=answer.id, status=MappingStatus.ANSWERED,
                confidence=max(0.9, answer.confidence), method=method,
                evidence=answer.evidence if _is_gemini_answer(answer) else [f"Detected answer label {answer.rawLabel or answer.normalizedLabel}"],
                regions=answer.regions,
            ))
            continue
        if len(exact) > 1:
            result.append(Mapping(
                questionId=question.id, answerId=None, status=MappingStatus.AMBIGUOUS,
                confidence=0.5, method=MappingMethod.AMBIGUOUS,
                evidence=["Multiple answers use the same normalized label"],
                regions=[region for answer in exact for region in answer.regions],
            ))
            continue

        unlabeled = [a for a in available.values() if not a.normalizedLabel]
        scores = sorted(
            ((_token_similarity(question.text, answer.text), answer) for answer in unlabeled),
            key=lambda pair: pair[0], reverse=True,
        )
        best_score = scores[0][0] if scores else 0.0
        margin = best_score - (scores[1][0] if len(scores) > 1 else 0.0)
        if scores and best_score >= config.semantic_threshold and margin >= config.ambiguity_margin:
            answer = scores[0][1]
            answer.status = AnswerStatus.MATCHED
            available.pop(answer.id)
            result.append(Mapping(
                questionId=question.id, answerId=answer.id, status=MappingStatus.ANSWERED,
                confidence=best_score, method=MappingMethod.SEMANTIC_MATCH,
                evidence=["Unlabelled answer content overlaps with the question"], regions=answer.regions,
            ))
        elif scores and best_score >= config.semantic_threshold - config.ambiguity_margin:
            result.append(Mapping(
                questionId=question.id, answerId=None, status=MappingStatus.AMBIGUOUS,
                confidence=best_score, method=MappingMethod.AMBIGUOUS,
                evidence=["An unlabelled answer is plausible but below the safe mapping threshold"],
                regions=scores[0][1].regions,
            ))
        else:
            result.append(Mapping(
                questionId=question.id, answerId=None, status=MappingStatus.UNANSWERED,
                confidence=1.0 if not scores else 1 - best_score, method=MappingMethod.NONE,
                evidence=["No answer met the configured mapping threshold"], regions=[],
            ))
    return result
