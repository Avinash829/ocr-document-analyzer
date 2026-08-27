import re


_PREFIX = re.compile(
    r"^\s*(?:ans(?:wer)?\s*[:.-]?\s*)?(?:(?:question|ques|q)\s*\.?\s*)?",
    re.I,
)
_LABEL = re.compile(
    r"^\s*(?P<number>\d{1,4})\s*(?:(?:[-.]?\s*\(?\s*(?P<part>[a-z]|[ivxlcdm]{1,6})\s*\)?)|[.)。])?\s*$",
    re.I,
)


def normalize_question_number(raw: str | None) -> str | None:
    """Conservatively normalize a question label without touching answer text."""
    if not raw:
        return None
    candidate = _PREFIX.sub("", raw.strip())
    match = _LABEL.fullmatch(candidate)
    if not match:
        return None
    number = str(int(match.group("number")))
    part = match.group("part")
    return f"{number}({part.lower()})" if part else number


def parent_number(normalized: str) -> str | None:
    match = re.fullmatch(r"(\d+)\([a-zivxlcdm]+\)", normalized)
    return match.group(1) if match else None


def label_prefix(text: str) -> tuple[str | None, str]:
    match = re.match(
        r"^\s*((?:(?:ans(?:wer)?|question|ques|q)\s*[:.-]?\s*)?\d{1,4}(?:(?:\s*\(\s*(?:[a-z]|[ivxlcdm]{1,6})\s*\))|(?:\s*-\s*(?:[a-z]|[ivxlcdm]{1,6}))|(?:[a-z]))?)[\s:.)。-]+(.+)$",
        text,
        re.I | re.S,
    )
    if not match:
        return None, text.strip()
    raw = match.group(1).strip()
    return (raw, match.group(2).strip()) if normalize_question_number(raw) else (None, text.strip())
