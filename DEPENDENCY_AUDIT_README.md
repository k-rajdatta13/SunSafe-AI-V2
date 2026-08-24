# Dependency audit helper

This is a read-only static audit. It does not change the environment.

From the SunSafe AI repository root:

    .\.venv\Scripts\python.exe evaluation\dependency_audit.py

Send the complete output back. We will use it to decide which dependencies
belong in runtime vs development requirements before changing any versions.

Do not uninstall or upgrade packages based on this report alone.
