import re
import uuid

from app.schemas.assessment import Question
from app.services.ocr import OcrLine
from app.utils.normalization import normalize_question_number, parent_number


_START = re.compile(r"^\s*((?:(?:question|ques|q)\s*\.?\s*)?\d{1,4}\s*(?:\(?\s*(?:[a-z]|[ivxlcdm]{1,6})\s*\)?|[-.)]))\s*(.*)$", re.I)
_MARKS = re.compile(r"(?:\[|\()(\d+(?:\.\d+)?)\s*(?:marks?)?(?:\]|\))\s*$", re.I)


def extract_questions(page_lines: list[tuple[int, int, int, list[OcrLine]]]) -> list[Question]:
    questions: list[Question] = []
    for page_number, page_width, page_height, lines in page_lines:
        current: Question | None = None
        for line in lines:
            match = _START.match(line.text)
            if match:
                raw_label, body = match.group(1).strip(), match.group(2).strip()
                normalized = normalize_question_number(raw_label)
                if not normalized or not body or len(body) < 3:
                    continue
                marks_match = _MARKS.search(body)
                marks = float(marks_match.group(1)) if marks_match else None
                text = _MARKS.sub("", body).strip()
                current = Question(
                    id=f"q_{uuid.uuid4().hex[:12]}", displayNumber=raw_label,
                    normalizedNumber=normalized, text=text, page=page_number, bbox=line.bbox,
                    pageWidth=page_width, pageHeight=page_height, order=len(questions),
                    parentId=parent_number(normalized), marks=marks, confidence=line.confidence,
                )
                questions.append(current)
                continue
            if current is None or not line.text.strip():
                continue
            lowered = line.text.strip().lower()
            if lowered.startswith(("instructions", "part ")) or lowered.startswith("page "):
                continue
            current.text = f"{current.text}\n{line.text.strip()}"
            current.confidence = min(current.confidence, line.confidence)
    return questions
