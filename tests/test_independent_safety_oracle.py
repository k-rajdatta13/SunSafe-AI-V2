from evaluation.independent_safety_oracle import expected


def test_oracle_uv_boundaries():
    assert expected(1.9, 25).uv_level == "LOW"
    assert expected(2.0, 25).uv_level == "LOW"
    assert expected(2.1, 25).uv_level == "MODERATE"
    assert expected(3.0, 25).uv_level == "MODERATE"
    assert expected(5.0, 25).uv_level == "MODERATE"
    assert expected(5.1, 25).uv_level == "HIGH"
    assert expected(7.0, 25).uv_level == "HIGH"
    assert expected(7.1, 25).uv_level == "VERY_HIGH"
    assert expected(8.0, 25).uv_level == "VERY_HIGH"


def test_oracle_protection_boundary():
    assert expected(2.9, 25).protection_required is False
    assert expected(3.0, 25).protection_required is True


def test_oracle_heat_boundaries():
    assert expected(0, 29.9).heat_caution == "LOW"
    assert expected(0, 30.0).heat_caution == "CAUTION"
    assert expected(0, 35.0).heat_caution == "CAUTION"
    assert expected(0, 35.1).heat_caution == "HIGH"


def test_oracle_hard_stop_priority():
    assert expected(8, 36).overall_action == "AVOID_PROLONGED_OUTDOOR_EXPOSURE"
    assert expected(8, 28).overall_action == "MINIMIZE_DIRECT_SUN_EXPOSURE"
