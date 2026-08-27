import io
from dataclasses import dataclass
from pathlib import Path

import pymupdf
from PIL import Image, ImageOps

from app.schemas.assessment import DocumentInfo, DocumentPage
from app.utils.files import ValidatedUpload


@dataclass(frozen=True)
class PageAsset:
    page: int
    path: Path
    width: int
    height: int


def render_document(upload: ValidatedUpload, output_dir: Path, url_prefix: str) -> tuple[DocumentInfo, list[PageAsset]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    assets: list[PageAsset] = []
    if upload.kind == "pdf":
        with pymupdf.open(stream=upload.content, filetype="pdf") as document:
            for index, page in enumerate(document):
                # Some scanner PDFs use pixel-like page dimensions. Blindly using
                # 2x rendering turned those into 5K images and exhausted Paddle's
                # native CPU tensors. Keep detail for normal PDFs while bounding
                # the longest edge for predictable memory use.
                scale = min(2.0, 2500.0 / max(page.rect.width, page.rect.height))
                pixmap = page.get_pixmap(matrix=pymupdf.Matrix(scale, scale), alpha=False)
                path = output_dir / f"page-{index + 1}.png"
                pixmap.save(path)
                assets.append(PageAsset(index + 1, path, pixmap.width, pixmap.height))
    else:
        with Image.open(io.BytesIO(upload.content)) as source:
            image = ImageOps.exif_transpose(source).convert("RGB")
            path = output_dir / "page-1.png"
            image.save(path, "PNG", optimize=True)
            assets.append(PageAsset(1, path, image.width, image.height))
    pages = [DocumentPage(page=a.page, width=a.width, height=a.height, imageUrl=f"{url_prefix}/{a.page}") for a in assets]
    return DocumentInfo(filename=upload.filename, pageCount=len(pages), pages=pages), assets
