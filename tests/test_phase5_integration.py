import pytest

from evaluation.live_integration import run_all


@pytest.mark.integration
def test_real_graph_integration_harness():
    result = run_all()
    assert result["all_harness_cases_passed"], result
    assert result["total_cases"] == 5
