import re
import uuid

from app.schemas.assessment import BoundingBox, Question
from app.services.ocr import OcrLine
from app.utils.normalization import normalize_question_number, parent_number


_START = re.compile(
    r"^\s*(?P<label>(?:(?:question|ques|q)\s*\.?\s*(?:(?:no|number)\s*\.?\s*)?|(?:no|number)\s*\.?\s*)?\d{1,4}(?:\s*(?:\(\s*(?:[a-z]|[ivxlcdm]{1,6})\s*\)|-\s*(?:[a-z]|[ivxlcdm]{1,6})|\.(?:[a-z]|[ivxlcdm]{1,6})))?)"
    r"\s*(?:[-:\u2013]\s*)?(?P<marks>\(\s*\d+(?:\.\d+)?\s*(?:marks?)?\s*\)|\[\s*\d+(?:\.\d+)?\s*(?:marks?)?\s*\]|\d+(?:\.\d+)?\s*marks?\b)?"
    r"\s*(?:[.:)\-\u2013]\s*)?(?P<body>.*)$",
    re.I,
)
_MARK_VALUE = re.compile(r"\d+(?:\.\d+)?")
_NON_QUESTION = re.compile(r"^(?:page\s+\d|instructions?\b|part\s+[ivx\d]|section\s+[a-z\d])", re.I)


def _expanded_bbox(first: BoundingBox, next_box: BoundingBox) -> BoundingBox:
    x1, y1 = min(first.x, next_box.x), min(first.y, next_box.y)
    x2 = max(first.x + first.width, next_box.x + next_box.width)
    y2 = max(first.y + first.height, next_box.y + next_box.height)
    return BoundingBox(x=x1, y=y1, width=x2 - x1, height=y2 - y1)


def extract_questions(page_lines: list[tuple[int, int, int, list[OcrLine]]]) -> list[Question]:
    """Extract numbered question blocks in printed order, including wrapped lines."""
    questions: list[Question] = []
    for page_number, page_width, page_height, lines in page_lines:
        current: Question | None = None
        for line in sorted(lines, key=lambda item: (item.bbox.y, item.bbox.x)):
            match = _START.match(line.text)
            label = match.group("label").strip() if match else None
            normalized = normalize_question_number(label)
            body = match.group("body").strip() if match else ""
            if normalized and (body or match.group("marks")):
                mark_text = match.group("marks") or ""
                mark_value = _MARK_VALUE.search(mark_text)
                current = Question(
                    id=f"q_{uuid.uuid4().hex[:12]}", displayNumber=label,
                    normalizedNumber=normalized, text=body, page=page_number, bbox=line.bbox,
                    pageWidth=page_width, pageHeight=page_height, order=len(questions),
                    parentId=parent_number(normalized), marks=float(mark_value.group()) if mark_value else None,
                    confidence=line.confidence,
                )
                questions.append(current)
                continue
            if current is None or not line.text.strip() or _NON_QUESTION.match(line.text.strip()):
                continue
            current.text = f"{current.text}\n{line.text.strip()}".strip()
            current.bbox = _expanded_bbox(current.bbox, line.bbox)
            current.confidence = min(current.confidence, line.confidence)
    return questions
