import time
from concurrent.futures import ThreadPoolExecutor

from app.services.ocr import PaddleOcrService


class ConcurrencyDetectingEngine:
    def __init__(self):
        self.active = 0
        self.max_active = 0

    def predict(self, *_args, **_kwargs):
        self.active += 1
        self.max_active = max(self.max_active, self.active)
        time.sleep(.02)
        self.active -= 1
        return []


def test_shared_paddle_predictor_is_never_invoked_concurrently(tmp_path):
    service = PaddleOcrService()
    engine = ConcurrencyDetectingEngine()
    service._engine = engine
    image = tmp_path / "page.png"
    image.write_bytes(b"unused by fake engine")
    with ThreadPoolExecutor(max_workers=3) as executor:
        list(executor.map(service.analyze, [image, image, image]))
    assert engine.max_active == 1
