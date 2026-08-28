import io
import re
import time

from fastapi.testclient import TestClient
from PIL import Image

from app.main import app
from app.schemas.assessment import BoundingBox


def image_bytes():
    stream = io.BytesIO()
    Image.new("RGB", (600, 800), "white").save(stream, "PNG")
    return stream.getvalue()


class FakeGemini:
    """A structured Gemini response fixture covering the production AI-only flow."""

    def analyze(self, prompt, _image_paths, schema):
        if schema.__name__ == "GeminiQuestionResponse":
            return schema.model_validate({"questions": [{
                "page_number": 1, "number": "1", "text": "Explain photosynthesis",
                "confidence": .95, "bbox_x": 50, "bbox_y": 50, "bbox_w": 500, "bbox_h": 100,
            }]})
        if schema.__name__ == "GeminiAnswerResponse":
            return schema.model_validate({"answers": [{
                "page_number": 1, "raw_question_reference": "1.", "question_number": "1",
                "answer_text": "Photosynthesis uses light.", "visual_elements": [],
                "confidence": .95, "bbox_x": 50, "bbox_y": 100, "bbox_w": 500, "bbox_h": 150,
            }]})
        answer_id = re.search(r"Answer id=(a_[a-f0-9]+)", prompt).group(1)
        return schema.model_validate({"mappings": [{
            "question_number": "Q1", "answer_id": answer_id, "status": "ANSWERED",
            "confidence": .95, "reasoning": "The visible answer label is 1.",
        }]})


def test_full_image_assessment_job():
    with TestClient(app) as client:
        fake_gemini = FakeGemini()
        original_gemini = client.app.state.jobs._gemini
        client.app.state.jobs._gemini = fake_gemini
        files = {
            "question_paper": ("questions.png", image_bytes(), "image/png"),
            "answer_sheet": ("answers.png", image_bytes(), "image/png"),
        }
        try:
            created = client.post("/api/assessments", files=files)
            assert created.status_code == 202
            identifier = created.json()["id"]
            for _ in range(50):
                job = client.get(f"/api/assessments/{identifier}").json()
                if job["processing"]["stage"] in {"COMPLETED", "DEGRADED", "ERROR"}:
                    break
                time.sleep(.02)
            result = client.get(f"/api/assessments/{identifier}/result")
            assert result.status_code == 200
            payload = result.json()
            assert payload["summary"]["answered"] == 1
            assert payload["mappings"][0]["answerId"] == payload["answers"][0]["id"]
            assert client.get(payload["answerSheet"]["pages"][0]["imageUrl"]).headers["content-type"] == "image/png"
        finally:
            client.app.state.jobs._gemini = original_gemini


def test_rejects_unsupported_upload():
    with TestClient(app) as client:
        response = client.post("/api/assessments", files={
            "question_paper": ("x.txt", b"text", "text/plain"),
            "answer_sheet": ("x.png", image_bytes(), "image/png"),
        })
        assert response.status_code == 422
        assert response.json()["detail"]["code"] == "UNSUPPORTED_FILE"
