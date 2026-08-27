import io
from dataclasses import dataclass
from pathlib import Path

import pymupdf
from PIL import Image, UnidentifiedImageError

from app.config import Settings


class FileValidationError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class ValidatedUpload:
    filename: str
    kind: str
    content: bytes
    page_count: int


def validate_upload(filename: str | None, content_type: str | None, content: bytes, settings: Settings) -> ValidatedUpload:
    safe_name = Path(filename or "upload").name
    if not content or len(content) > settings.max_file_size_mb * 1024 * 1024:
        raise FileValidationError("INVALID_FILE_SIZE", f"File must be between 1 byte and {settings.max_file_size_mb} MB.")
    extension = Path(safe_name).suffix.lower()
    if content.startswith(b"%PDF-"):
        if extension != ".pdf" or content_type not in {"application/pdf", "application/octet-stream"}:
            raise FileValidationError("FILE_TYPE_MISMATCH", "The PDF extension, content type, and file signature do not agree.")
        try:
            with pymupdf.open(stream=content, filetype="pdf") as document:
                if document.needs_pass:
                    raise FileValidationError("ENCRYPTED_PDF", "Password-protected PDFs are not supported.")
                page_count = document.page_count
                for page in document:
                    _ = page.rect
        except FileValidationError:
            raise
        except Exception as exc:
            raise FileValidationError("CORRUPTED_PDF", "The PDF is corrupted or unreadable.") from exc
        kind = "pdf"
    else:
        if extension not in {".png", ".jpg", ".jpeg", ".webp"} or not (content_type or "").startswith("image/"):
            raise FileValidationError("UNSUPPORTED_FILE", "Upload a PDF, PNG, JPEG, or WebP file.")
        try:
            with Image.open(io.BytesIO(content)) as image:
                image.verify()
            with Image.open(io.BytesIO(content)) as image:
                width, height = image.size
                if max(width, height) > settings.max_image_dimension:
                    raise FileValidationError("IMAGE_TOO_LARGE", "Image dimensions exceed the configured limit.")
        except FileValidationError:
            raise
        except (UnidentifiedImageError, OSError) as exc:
            raise FileValidationError("CORRUPTED_IMAGE", "The image is corrupted or unreadable.") from exc
        kind, page_count = "image", 1
    if page_count < 1 or page_count > settings.max_pages:
        raise FileValidationError("PAGE_LIMIT", f"Documents may contain at most {settings.max_pages} pages.")
    return ValidatedUpload(safe_name, kind, content, page_count)
