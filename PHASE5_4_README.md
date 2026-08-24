# SunSafe AI V2 — Phase 5.4 Independent Safety Oracle (Corrected)

The first Phase 5.4 patch exposed two issues in the evaluation patch itself:

1. The boundary test incorrectly treated UVI 2.9 as LOW. The production policy and its documentation define LOW as UVI <= 2, so 2.9 is MODERATE.
2. `run_safety_oracle.py` was not directly executable from the repository root because its import path did not add the project root before importing `evaluation.*`.

This corrected patch fixes both issues without changing the production safety policy.

## Independent policy

The oracle independently encodes:
- UVI <= 2: LOW
- 2 < UVI <= 5: MODERATE
- 5 < UVI <= 7: HIGH
- UVI > 7: VERY_HIGH
- protection required at UVI >= 3
- temperature < 30 C: LOW
- 30 C <= temperature <= 35 C: CAUTION
- temperature > 35 C: HIGH
- hard stop for VERY_HIGH UV or HIGH heat
- HIGH heat takes action priority over VERY_HIGH UV

The oracle does not import `utils.safety_policy`.

## Replace / add

Replace:
- `evaluation/safety_eval.py`

Add:
- `evaluation/independent_safety_oracle.py`
- `evaluation/run_safety_oracle.py`
- `tests/test_independent_safety_oracle.py`

## Run

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_independent_safety_oracle.py -q
.\.venv\Scripts\python.exe evaluation\run_safety_oracle.py
```

A passing result means the production implementation matches the independently encoded project policy specification. It is not a claim of clinical validation or real-world medical accuracy.
