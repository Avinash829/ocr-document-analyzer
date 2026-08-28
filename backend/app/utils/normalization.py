import re


_LABEL = re.compile(
    r"^\s*(?P<number>\d{1,4})\s*(?:(?:-\s*\(?\s*(?P<hyphen_part>[a-z]|[ivxlcdm]{1,6})\s*\)?)|(?:\.(?P<dot_part>[a-z]|[ivxlcdm]{1,6}))|(?:\s*:\s*(?P<colon_part>[a-z]|[ivxlcdm]{1,6}))|\(\s*(?P<parenthesized_part>[a-z]|[ivxlcdm]{1,6})\s*\)|(?P<joined_part>[a-z])|[.)\u3002:\-])?\s*$",
    re.I,
)
_ANSWER_PREFIX = re.compile(r"^\s*(?:ans(?:wer)?\s*[:.-]?\s*)", re.I)
_QUESTION_PREFIX = re.compile(r"^\s*(?:(?:question|ques|q)\s*\.?\s*(?:(?:no|number)\s*\.?\s*)?|(?:no|number)\s*\.?\s*)", re.I)


def normalize_question_number(raw: str | None) -> str | None:
    """Conservatively normalize an explicit label without changing answer text."""
    if not raw:
        return None
    candidate = _ANSWER_PREFIX.sub("", raw.strip())
    candidate = _QUESTION_PREFIX.sub("", candidate)
    match = _LABEL.fullmatch(candidate)
    if not match:
        return None
    number = str(int(match.group("number")))
    part = match.group("hyphen_part") or match.group("dot_part") or match.group("colon_part") or match.group("parenthesized_part") or match.group("joined_part")
    return f"{number}({part.lower()})" if part else number


def parent_number(normalized: str) -> str | None:
    match = re.fullmatch(r"(\d+)\([a-zivxlcdm]+\)", normalized)
    return match.group(1) if match else None


def label_prefix(text: str) -> tuple[str | None, str]:
    match = re.match(
        r"^\s*((?:(?:ans(?:wer)?|question|ques|q)\s*[:.-]?\s*)?\d{1,4}(?:(?:\s*\(\s*(?:[a-z]|[ivxlcdm]{1,6})\s*\))|(?:\s*-\s*(?:[a-z]|[ivxlcdm]{1,6}))|(?:\.(?:[a-z]|[ivxlcdm]{1,6}))|(?:[a-z]))?)[\s:.)\u3002\-\u2013]*(.*)$",
        text,
        re.I | re.S,
    )
    if not match:
        return None, text.strip()
    raw = match.group(1).strip()
    return (raw, match.group(2).strip()) if normalize_question_number(raw) else (None, text.strip())
