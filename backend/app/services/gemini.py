import logging
import time
from enum import StrEnum
from pathlib import Path
from typing import TypeVar

from google import genai
from google.genai import types
from pydantic import BaseModel

from app.services.gemini_key_pool import GeminiKeyPool

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)


class GeminiErrorCategory(StrEnum):
    RETRYABLE_TRANSIENT = "RETRYABLE_TRANSIENT"
    CREDENTIAL_FAILURE = "CREDENTIAL_FAILURE"
    NON_RETRYABLE_REQUEST_ERROR = "NON_RETRYABLE_REQUEST_ERROR"


class GeminiServiceError(RuntimeError):
    def __init__(self, category: GeminiErrorCategory, message: str):
        super().__init__(message)
        self.category = category


def classify_error(exc: Exception) -> GeminiErrorCategory:
    status = getattr(exc, "status_code", None) or getattr(exc, "code", None)
    text = str(exc).lower()
    if status in {401, 403} or any(term in text for term in ("api key not valid", "unauthenticated", "permission denied")):
        return GeminiErrorCategory.CREDENTIAL_FAILURE
    if status in {408, 429, 500, 502, 503, 504} or any(term in text for term in ("timeout", "temporarily unavailable", "resource exhausted")):
        return GeminiErrorCategory.RETRYABLE_TRANSIENT
    return GeminiErrorCategory.NON_RETRYABLE_REQUEST_ERROR


class GeminiService:
    def __init__(self, pool: GeminiKeyPool, model: str, max_attempts: int = 3, timeout_seconds: int = 90):
        self.pool, self.model = pool, model
        self.max_attempts, self.timeout_seconds = max_attempts, timeout_seconds

    def analyze(self, prompt: str, image_paths: list[Path], schema: type[T]) -> T:
        if not len(self.pool):
            raise GeminiServiceError(GeminiErrorCategory.CREDENTIAL_FAILURE, "No Gemini API keys are configured.")
        excluded: set[int] = set()
        last_error: GeminiServiceError | None = None
        for attempt in range(1, self.max_attempts + 1):
            key = self.pool.acquire(excluded)
            if key is None:
                break
            excluded.add(key.index)
            started = time.monotonic()
            try:
                client = genai.Client(api_key=key.secret, http_options=types.HttpOptions(timeout=self.timeout_seconds * 1000))
                parts = [prompt]
                for path in image_paths:
                    parts.append(types.Part.from_bytes(data=path.read_bytes(), mime_type="image/png"))
                response = client.models.generate_content(
                    model=self.model, contents=parts,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json", response_json_schema=schema.model_json_schema(),
                        temperature=0,
                    ),
                )
                parsed = schema.model_validate_json(response.text)
                self.pool.report_success(key.index)
                logger.info("gemini_success", extra={"key_index": key.index, "attempt": attempt, "duration": time.monotonic() - started})
                return parsed
            except Exception as exc:
                category = classify_error(exc)
                last_error = GeminiServiceError(category, "Gemini analysis failed.")
                self.pool.report_failure(key.index, credential=category == GeminiErrorCategory.CREDENTIAL_FAILURE)
                logger.warning("gemini_failure", extra={"key_index": key.index, "attempt": attempt, "category": category, "duration": time.monotonic() - started})
                if category == GeminiErrorCategory.NON_RETRYABLE_REQUEST_ERROR:
                    raise last_error from exc
                if attempt < self.max_attempts:
                    time.sleep(min(2 ** (attempt - 1), 4))
        raise last_error or GeminiServiceError(GeminiErrorCategory.RETRYABLE_TRANSIENT, "All available Gemini keys are cooling down.")

