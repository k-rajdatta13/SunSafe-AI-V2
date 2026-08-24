"""
SunSafe AI dependency usage audit.

Run from repository root:
    python evaluation/dependency_audit.py

This script does not install, uninstall, or modify packages.
It statically compares direct requirements against Python imports and reports:
- runtime-looking dependencies used by source
- declared packages with no detected imports
- imports whose distribution mapping is ambiguous
- test-only imports
- requirements files discovered

It intentionally treats this as a review aid, not proof that a package is
safe to remove: dynamic imports, plugins, optional extras, and CLI-only usage
can evade static analysis.
"""
from __future__ import annotations

import ast
import importlib.metadata as md
from pathlib import Path
import re
import sys
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[1]
EXCLUDE_DIRS = {".venv", "venv", "__pycache__", ".git", "node_modules"}
SOURCE_DIRS = ["api", "agents", "rag", "tools", "evaluation", "tests"]

# Conservative stdlib list for Python 3.11; third-party imports are resolved
# through installed distribution metadata when possible.
STDLIB = {
    "abc","argparse","ast","asyncio","base64","bisect","calendar","collections",
    "contextlib","copy","csv","dataclasses","datetime","decimal","enum","errno",
    "functools","glob","hashlib","heapq","html","http","importlib","inspect",
    "io","itertools","json","logging","math","mimetypes","numbers","os","pathlib",
    "pickle","platform","pprint","random","re","secrets","shlex","shutil",
    "signal","sqlite3","statistics","string","subprocess","sys","tempfile",
    "textwrap","threading","time","timeit","traceback","types","typing","uuid",
    "warnings","weakref","xml","zipfile",
}

# Common PyPI distribution -> import-package names not reliably recoverable
# from metadata alone.
KNOWN = {
    "beautifulsoup4": {"bs4"},
    "scikit-learn": {"sklearn"},
    "python-dotenv": {"dotenv"},
    "langchain-core": {"langchain_core"},
    "langchain-google-genai": {"langchain_google_genai"},
    "langgraph": {"langgraph"},
    "uvicorn": {"uvicorn"},
    "fastapi": {"fastapi"},
    "pydantic": {"pydantic"},
    "requests": {"requests"},
    "numpy": {"numpy"},
    "streamlit": {"streamlit"},
    "pytest": {"pytest"},
}

def req_names(path: Path) -> list[str]:
    if not path.exists():
        return []
    result = []
    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith(("-", "git+", "http")):
            continue
        # Strip environment markers/extras/version specifiers.
        name = re.split(r"[<>=!~;\[\s]", line, maxsplit=1)[0].lower()
        if name:
            result.append(name)
    return result

def python_files():
    for top in SOURCE_DIRS:
        root = ROOT / top
        if not root.exists():
            continue
        for p in root.rglob("*.py"):
            if not any(part in EXCLUDE_DIRS for part in p.parts):
                yield p

def imports_from(path: Path):
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
    except SyntaxError as exc:
        return {f"<SYNTAX ERROR: {exc}>"}  # surfaced, not hidden
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.add(node.module.split(".")[0])
    return found

def distribution_imports():
    mapping = defaultdict(set)
    for dist in md.distributions():
        name = (dist.metadata.get("Name") or "").lower()
        if not name:
            continue
        top_level = dist.read_text("top_level.txt")
        if top_level:
            for line in top_level.splitlines():
                if line.strip():
                    mapping[name].add(line.strip())
    for dist, mods in KNOWN.items():
        mapping[dist].update(mods)
    return mapping

def main():
    req_files = [ROOT / "requirements.txt", ROOT / "requirements-dev.txt"]
    req_files += sorted(ROOT.glob("requirements-*.txt"))

    files = list(python_files())
    used = defaultdict(set)
    for f in files:
        for mod in imports_from(f):
            if mod not in STDLIB:
                used[mod].add(str(f.relative_to(ROOT)))

    dist_map = distribution_imports()

    print("=== SunSafe AI Dependency Usage Audit ===")
    print(f"Repository: {ROOT}")
    print(f"Python: {sys.version.split()[0]}")
    print(f"Python source files scanned: {len(files)}")
    print()

    for req in req_files:
        names = req_names(req)
        if not names:
            continue
        print(f"--- {req.relative_to(ROOT)} ---")
        for name in names:
            mods = dist_map.get(name, set())
            matched = sorted(m for m in mods if m in used)
            if matched:
                print(f"USED       {name:<30} imports: {', '.join(matched)}")
            else:
                print(f"NOT-DETECTED {name:<28} (may be optional/dynamic/test-only)")
        print()

    print("--- Third-party imports not mapped to a declared distribution ---")
    declared = set()
    for req in req_files:
        declared.update(req_names(req))
    unmapped = []
    for mod, files_used in sorted(used.items()):
        candidates = [
            name for name, mods in dist_map.items() if mod in mods
        ]
        if not candidates:
            unmapped.append((mod, sorted(files_used)))
    if unmapped:
        for mod, files_used in unmapped:
            print(f"{mod:<25} {files_used[0]}")
    else:
        print("None detected.")
    print()

    print("NOTE: 'NOT-DETECTED' is not proof that a dependency is unused.")
    print("Review dynamic imports, optional integrations, CLI entry points,")
    print("and framework/plugin metadata before removing anything.")

if __name__ == "__main__":
    main()
