import pytest
from pydantic import ValidationError

from app.schemas.assessment import BoundingBox, Region
from app.utils.coordinates import css_box, validated_region


def test_coordinate_conversion_is_scale_independent():
    region = Region(page=1, bbox=BoundingBox(x=100, y=200, width=300, height=400), pageWidth=1000, pageHeight=2000)
    assert css_box(region) == {"left": 10, "top": 10, "width": 30, "height": 20}


def test_rounding_overflow_is_clamped():
    region = validated_region(1, BoundingBox(x=10, y=10, width=90.5, height=90.5), 100, 100)
    assert region.bbox.width == 90


def test_material_overflow_is_rejected():
    with pytest.raises((ValueError, ValidationError)):
        validated_region(1, BoundingBox(x=10, y=10, width=92, height=90), 100, 100)

