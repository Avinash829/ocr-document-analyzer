from app.schemas.assessment import BoundingBox, Region


def validated_region(page: int, bbox: BoundingBox, page_width: float, page_height: float) -> Region:
    """Clamp only sub-pixel/rounding overflow; reject materially invalid regions."""
    overflow_x = bbox.x + bbox.width - page_width
    overflow_y = bbox.y + bbox.height - page_height
    if overflow_x > 1 or overflow_y > 1:
        raise ValueError("region materially exceeds page bounds")
    clamped = BoundingBox(
        x=min(bbox.x, page_width),
        y=min(bbox.y, page_height),
        width=min(bbox.width, page_width - bbox.x),
        height=min(bbox.height, page_height - bbox.y),
    )
    return Region(page=page, bbox=clamped, pageWidth=page_width, pageHeight=page_height)


def css_box(region: Region) -> dict[str, float]:
    box = region.bbox
    return {
        "left": box.x / region.pageWidth * 100,
        "top": box.y / region.pageHeight * 100,
        "width": box.width / region.pageWidth * 100,
        "height": box.height / region.pageHeight * 100,
    }

