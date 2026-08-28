import pytest

from app.utils.normalization import label_prefix, normalize_question_number, parent_number


@pytest.mark.parametrize(("raw", "expected"), [
    ("Q1", "1"), ("Q.1", "1"), ("Question 01", "1"), ("Question No. 01", "1"),
    ("Q. No. 1", "1"), ("No. 1", "1"), ("1:", "1"), ("1-", "1"),
    ("11 (a)", "11(a)"), ("11-a", "11(a)"), ("11.a", "11(a)"),
    ("Q11(ii)", "11(ii)"), ("Ans 3a", "3(a)"), ("21\u3002", "21"),
])
def test_normalizes_supported_labels(raw, expected):
    assert normalize_question_number(raw) == expected


@pytest.mark.parametrize("raw", ["", "section A", "page 1 of 2", "answer", "1 plus 2", "2 major applications"])
def test_rejects_non_labels(raw):
    assert normalize_question_number(raw) is None


def test_preserves_answer_text_while_extracting_prefix():
    assert label_prefix("Ans 11 (a): Photosynthesis uses light") == ("Ans 11 (a)", "Photosynthesis uses light")
    assert parent_number("11(a)") == "11"
