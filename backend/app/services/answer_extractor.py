import re
import uuid
from dataclasses import dataclass

from app.schemas.assessment import Answer, BoundingBox
from app.services.ocr import OcrLine
from app.utils.coordinates import validated_region
from app.utils.normalization import label_prefix, normalize_question_number


@dataclass(frozen=True)
class LabelAnchor:
    raw: str
    normalized: str
    line: OcrLine
    inline_text: str

    @property
    def center_y(self) -> float:
        return self.line.bbox.y + self.line.bbox.height / 2


def _normalise_left_column_label(line: OcrLine, page_width: int) -> tuple[str | None, str]:
    """Recognise explicit answer labels, with narrow OCR corrections at the label."""
    # Relaxed from 15% to 40% to account for wide handwritten margins or indented numbers
    if line.bbox.x > page_width * 0.40:
        return None, ""
    raw, inline_text = label_prefix(line.text)
    explicit = re.match(r"^\s*(?:ans(?:wer)?|question|ques|q)\b", line.text, re.I) or re.match(
        r"^\s*\d{1,4}\s*(?:[.)\u3002:]|[-\u2013]\s*[a-z]?(?:\s|$)|\([a-zivxlcdm]+\))", line.text, re.I
    )
    if raw and explicit:
        return raw, inline_text
    normalized = normalize_question_number(line.text)
    if normalized:
        return line.text.strip(), ""
    corrected = line.text.strip()
    if len(corrected) <= 4:
        corrected = corrected.replace("S", "5").replace("s", "5").replace("O", "0")
        if normalize_question_number(corrected):
            return corrected, ""
    return None, ""


def _region_for_lines(page: int, lines: list[OcrLine], page_width: int, page_height: int):
    x1 = min(line.bbox.x for line in lines)
    y1 = min(line.bbox.y for line in lines)
    x2 = max(line.bbox.x + line.bbox.width for line in lines)
    y2 = max(line.bbox.y + line.bbox.height for line in lines)
    return validated_region(page, BoundingBox(x=x1, y=y1, width=x2 - x1, height=y2 - y1), page_width, page_height)


def _answers_for_page(page_number: int, page_width: int, page_height: int, lines: list[OcrLine]) -> list[Answer]:
    ordered = sorted(lines, key=lambda line: (line.bbox.y + line.bbox.height / 2, line.bbox.x))
    anchors: list[LabelAnchor] = []
    anchor_lines: set[int] = set()
    for index, line in enumerate(ordered):
        raw, inline_text = _normalise_left_column_label(line, page_width)
        normalized = normalize_question_number(raw)
        if normalized:
            anchors.append(LabelAnchor(raw=raw, normalized=normalized, line=line, inline_text=inline_text))
            anchor_lines.add(index)

    answers: list[Answer] = []
    for anchor_index, anchor in enumerate(anchors):
        # Exclude top-of-page noise by setting a max distance for the first anchor
        if anchor_index == 0:
            upper = anchor.line.bbox.y - (anchor.line.bbox.height * 2.5)
        else:
            upper = (anchors[anchor_index - 1].center_y + anchor.center_y) / 2
            
        lower = float("inf") if anchor_index == len(anchors) - 1 else (anchor.center_y + anchors[anchor_index + 1].center_y) / 2
        content = [
            line for line_index, line in enumerate(ordered)
            if line_index not in anchor_lines
            and upper <= line.bbox.y + line.bbox.height / 2 < lower
            # Allow text to be slightly left of the anchor in case of messy indentation
            and line.bbox.x >= anchor.line.bbox.x - (page_width * 0.20)
        ]
        text_parts = [anchor.inline_text, *(line.text for line in content)]
        region_lines = [anchor.line, *content]
        answers.append(Answer(
            id=f"a_{uuid.uuid4().hex[:12]}", rawLabel=anchor.raw, normalizedLabel=anchor.normalized,
            text="\n".join(part for part in text_parts if part).strip(),
            regions=[_region_for_lines(page_number, region_lines, page_width, page_height)], pages=[page_number],
            confidence=min(line.confidence for line in region_lines), evidence=[f"OCR detected left-column label {anchor.raw}"],
        ))
    return answers


def extract_answers(page_lines: list[tuple[int, int, int, list[OcrLine]]]) -> list[Answer]:
    """Segment labelled answers by layout bands rather than OCR iteration order."""
    return [answer for page in page_lines for answer in _answers_for_page(*page)]
