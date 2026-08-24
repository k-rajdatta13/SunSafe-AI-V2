# Dependency Fix — Python 3.11

The previous final-audit archive contained a generated pip-freeze-style
requirements file with `numpy==2.5.1`, which is not installable on Python 3.11.
That made the clean Windows installation non-reproducible.

This release replaces those generated transitive pins with direct application
dependencies and compatible version ranges for the supported Python 3.11
environment.

Use:

    .\.venv\Scripts\python.exe -m pip install -r requirements.txt

Then:

    .\.venv\Scripts\python.exe -m pytest -q

Do not manually install NumPy or pytest separately.
