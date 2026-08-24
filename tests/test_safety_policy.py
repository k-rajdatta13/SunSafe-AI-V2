import pytest

from utils.safety_policy import (
    build_safety_assessment,
    classify_uv,
    protection_required,
)


def test_uv_bands():
    assert classify_uv(0) == "LOW"
    assert classify_uv(2) == "LOW"
    assert classify_uv(3) == "MODERATE"
    assert classify_uv(7) == "HIGH"
    assert classify_uv(8) == "VERY_HIGH"


def test_protection_threshold():
    assert protection_required(2.9) is False
    assert protection_required(3) is True


def test_high_uv_is_hard_stop():
    assessment = build_safety_assessment(uv_index=8, temperature_c=28, age=25)
    assert assessment.hard_stop is True
    assert assessment.overall_action == "MINIMIZE_DIRECT_SUN_EXPOSURE"


def test_high_heat_is_hard_stop():
    assessment = build_safety_assessment(uv_index=2, temperature_c=36, age=25)
    assert assessment.hard_stop is True
    assert assessment.overall_action == "AVOID_PROLONGED_OUTDOOR_EXPOSURE"


def test_negative_uv_rejected():
    with pytest.raises(ValueError):
        classify_uv(-1)
