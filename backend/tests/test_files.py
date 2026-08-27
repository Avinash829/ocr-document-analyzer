import io

import pymupdf
import pytest
from PIL import Image

from app.config import Settings
from app.utils.files import FileValidationError, validate_upload


def png_bytes():
    stream = io.BytesIO()
    Image.new("RGB", (100, 200), "white").save(stream, "PNG")
    return stream.getvalue()


def pdf_bytes():
    document = pymupdf.open()
    document.new_page()
    content = document.tobytes()
    document.close()
    return content


def test_validates_actual_image_and_pdf_structure():
    settings = Settings()
    assert validate_upload("paper.png", "image/png", png_bytes(), settings).page_count == 1
    assert validate_upload("paper.pdf", "application/pdf", pdf_bytes(), settings).kind == "pdf"


def test_rejects_extension_signature_mismatch_and_corruption():
    settings = Settings()
    with pytest.raises(FileValidationError) as mismatch:
        validate_upload("paper.jpg", "image/jpeg", b"%PDF-not-real", settings)
    assert mismatch.value.code == "FILE_TYPE_MISMATCH"
    with pytest.raises(FileValidationError) as corrupt:
        validate_upload("paper.png", "image/png", b"not an image", settings)
    assert corrupt.value.code == "CORRUPTED_IMAGE"
