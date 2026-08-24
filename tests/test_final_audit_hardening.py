from pathlib import Path
import pytest
from utils.retry import with_retry

ROOT = Path(__file__).resolve().parents[1]

def test_obsolete_v1_exposure_rules_removed():
    assert not (ROOT / "utils" / "rules.py").exists()

def test_retry_rejects_invalid_attempt_count():
    with pytest.raises(ValueError):
        with_retry(lambda: True, attempts=0)
