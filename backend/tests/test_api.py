import io
import time

from fastapi.testclient import TestClient
from PIL import Image

from app.main import app
from app.schemas.assessment import BoundingBox
from app.services.ocr import OcrLine


def image_bytes():
    stream = io.BytesIO()
    Image.new("RGB", (600, 800), "white").save(stream, "PNG")
    return stream.getvalue()


class FakeOcr:
    calls = 0

    def analyze(self, _path):
        self.calls += 1
        text = "1. Explain photosynthesis" if self.calls == 1 else "Ans 1 Photosynthesis uses light"
        return [OcrLine(text, .95, BoundingBox(x=30, y=50, width=300, height=40))]


def test_full_image_assessment_job():
    with TestClient(app) as client:
        client.app.state.jobs.ocr = FakeOcr()
        files = {
            "question_paper": ("questions.png", image_bytes(), "image/png"),
            "answer_sheet": ("answers.png", image_bytes(), "image/png"),
        }
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


def test_rejects_unsupported_upload():
    with TestClient(app) as client:
        response = client.post("/api/assessments", files={
            "question_paper": ("x.txt", b"text", "text/plain"),
            "answer_sheet": ("x.png", image_bytes(), "image/png"),
        })
        assert response.status_code == 422
        assert response.json()["detail"]["code"] == "UNSUPPORTED_FILE"

