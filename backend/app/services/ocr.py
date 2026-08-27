import logging
from dataclasses import dataclass
from pathlib import Path
from threading import RLock

from app.schemas.assessment import BoundingBox

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class OcrLine:
    text: str
    confidence: float
    bbox: BoundingBox


class OcrUnavailableError(RuntimeError):
    pass


class PaddleOcrService:
    """Lazy local PaddleOCR adapter; models load once and never at API import time."""
    def __init__(self):
        self._engine = None
        # Paddle predictors retain mutable native tensors and are not thread-safe.
        # One service instance may be shared by multiple background jobs, so both
        # model creation and inference must be serialized.
        self._lock = RLock()

    def _get_engine(self):
        with self._lock:
            if self._engine is None:
                try:
                    from paddleocr import PaddleOCR
                except ImportError as exc:
                    raise OcrUnavailableError("PaddleOCR is not installed in this runtime.") from exc
                self._engine = PaddleOCR(
                    lang="en",
                    use_doc_orientation_classify=False,
                    use_doc_unwarping=False,
                    use_textline_orientation=False,
                )
            return self._engine

    def analyze(self, path: Path) -> list[OcrLine]:
        try:
            with self._lock:
                results = self._get_engine().predict(
                    str(path),
                    use_doc_orientation_classify=False,
                    use_doc_unwarping=False,
                    use_textline_orientation=False,
                )
        except OcrUnavailableError:
            raise
        except Exception as exc:
            raise RuntimeError("OCR inference failed.") from exc
        lines: list[OcrLine] = []
        for result in results:
            data = getattr(result, "json", None)
            data = data() if callable(data) else data
            if isinstance(data, dict) and "res" in data:
                data = data["res"]
            if not isinstance(data, dict):
                continue
            texts = data.get("rec_texts", [])
            scores = data.get("rec_scores", [])
            boxes = data.get("rec_boxes", data.get("dt_polys", []))
            for text, score, box in zip(texts, scores, boxes):
                coords = list(box)
                if len(coords) == 4 and not hasattr(coords[0], "__len__"):
                    x1, y1, x2, y2 = map(float, coords)
                else:
                    points = [point for point in coords]
                    xs, ys = [float(p[0]) for p in points], [float(p[1]) for p in points]
                    x1, y1, x2, y2 = min(xs), min(ys), max(xs), max(ys)
                if text.strip() and x2 > x1 and y2 > y1:
                    lines.append(OcrLine(text.strip(), float(score), BoundingBox(x=x1, y=y1, width=x2-x1, height=y2-y1)))
        return sorted(lines, key=lambda line: (line.bbox.y, line.bbox.x))
