from app.schemas.assessment import Answer, Question
from app.services.mapping import map_answers
from app.services.answer_extractor import extract_answers
from app.services.ocr import OcrLine
from app.schemas.assessment import BoundingBox
from app.services.question_extractor import extract_questions


def question(identifier, number, order=0, text="Explain photosynthesis light energy chlorophyll"):
    return Question(id=identifier, displayNumber=number, normalizedNumber=number, text=text, page=1, order=order)


def answer(identifier, label=None, text="", regions=None):
    return Answer(id=identifier, rawLabel=label, normalizedLabel=label, text=text, regions=regions or [], pages=[], confidence=.9)


def test_out_of_order_explicit_mapping_and_unanswered():
    mappings = map_answers(
        [question("q1", "1", 0), question("q2", "2", 1)],
        [answer("a2", "2"), answer("a1", "1")],
    )
    assert [mapping.answerId for mapping in mappings] == ["a1", "a2"]
    assert all(mapping.status == "ANSWERED" for mapping in mappings)


def test_unanswered_and_unmatched_are_not_fabricated():
    answers = [answer("extra", "99", "unrelated")]
    mapping = map_answers([question("q1", "1")], answers)[0]
    assert mapping.status == "UNANSWERED"
    assert mapping.answerId is None and not mapping.regions
    assert answers[0].status == "UNMATCHED"


def test_duplicate_labels_are_ambiguous():
    mapping = map_answers([question("q1", "1")], [answer("a1", "1"), answer("a2", "1")])[0]
    assert mapping.status == "AMBIGUOUS"
    assert mapping.method == "AMBIGUOUS"


def test_high_confidence_unlabelled_semantic_match():
    q = question("q1", "1", text="light energy chlorophyll photosynthesis glucose oxygen")
    a = answer("a1", text="photosynthesis uses light energy and chlorophyll to make glucose and oxygen")
    mapping = map_answers([q], [a])[0]
    assert mapping.status == "ANSWERED"
    assert mapping.method == "SEMANTIC_MATCH"


def test_label_only_ocr_region_starts_answer_segment():
    lines = [
        OcrLine("21.", .92, BoundingBox(x=10, y=20, width=30, height=20)),
        OcrLine("Supervised learning uses labelled data", .9, BoundingBox(x=60, y=20, width=300, height=20)),
        OcrLine("23.", .88, BoundingBox(x=10, y=80, width=30, height=20)),
    ]
    answers = extract_answers([(1, 600, 800, lines)])
    assert [item.normalizedLabel for item in answers] == ["21", "23"]
    assert answers[0].text == "Supervised learning uses labelled data"
    assert answers[1].text == ""


def test_layout_bands_keep_answer_two_out_of_answer_one_region():
    lines = [
        OcrLine("C", .9, BoundingBox(x=175, y=296, width=61, height=75)),
        OcrLine("1.", .9, BoundingBox(x=28, y=304, width=83, height=76)),
        OcrLine("C", .9, BoundingBox(x=185, y=419, width=50, height=68)),
        OcrLine("2.", .9, BoundingBox(x=31, y=423, width=89, height=71)),
    ]
    answers = extract_answers([(1, 1786, 2525, lines)])
    assert [item.normalizedLabel for item in answers] == ["1", "2"]
    assert [item.text for item in answers] == ["C", "C"]
    assert answers[0].regions[0].bbox.y + answers[0].regions[0].bbox.height < answers[1].regions[0].bbox.y


def test_ideographic_stop_label_splits_the_next_handwritten_answer():
    lines = [
        OcrLine("B", .9, BoundingBox(x=175, y=541, width=55, height=66)),
        OcrLine("20.", .9, BoundingBox(x=0, y=561, width=96, height=70)),
        OcrLine("Supervised Learning is a type of machine", .9, BoundingBox(x=174, y=648, width=1400, height=96)),
        OcrLine("21。", .9, BoundingBox(x=15, y=684, width=94, height=53)),
        OcrLine("learning that are used to train and predict", .9, BoundingBox(x=172, y=743, width=1500, height=109)),
    ]
    answers = extract_answers([(2, 1786, 2525, lines)])
    assert [item.normalizedLabel for item in answers] == ["20", "21"]
    assert answers[0].text == "B"
    assert answers[1].text.startswith("Supervised Learning")


def test_question_parser_supports_q_number_with_marks_and_wrapped_text():
    lines = [
        OcrLine("Q1 (5 Marks)", .99, BoundingBox(x=20, y=100, width=100, height=20)),
        OcrLine("Two taps A and B fill a tank.", .99, BoundingBox(x=20, y=125, width=250, height=20)),
        OcrLine("Q2 (5 Marks)", .99, BoundingBox(x=20, y=200, width=100, height=20)),
        OcrLine("A father and his son have x and y coins.", .99, BoundingBox(x=20, y=225, width=300, height=20)),
    ]
    questions = extract_questions([(1, 595, 842, lines)])
    assert [(item.normalizedNumber, item.marks) for item in questions] == [("1", 5), ("2", 5)]
    assert questions[0].text == "Two taps A and B fill a tank."


def test_question_parser_supports_unbracketed_marks_after_a_dash():
    line = OcrLine("Question No. 2 - 5 marks: Explain the method.", .99, BoundingBox(x=20, y=100, width=300, height=20))
    question = extract_questions([(1, 595, 842, [line])])[0]
    assert (question.normalizedNumber, question.marks, question.text) == ("2", 5, "Explain the method.")
