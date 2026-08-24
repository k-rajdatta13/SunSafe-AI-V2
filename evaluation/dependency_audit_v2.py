"""
SunSafe AI dependency audit v2.

Run from repository root:
    python -m evaluation.dependency_audit_v2

Read-only: does not install, uninstall, upgrade, or modify packages.

Improvements over v1:
- scans root-level .py files as well as api/agents/rag/tools/evaluation/tests
- uses importlib.metadata.packages_distributions() to map import names to PyPI
  distributions, which is more reliable for packages such as langgraph,
  sentence-transformers and qdrant-client
- reports where each import was found
- separates production-looking code from tests/evaluation
- compares every requirements*.txt file independently
"""

from __future__ import annotations

import ast
import importlib.metadata as md
from pathlib import Path
from collections import defaultdict
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
EXCLUDE = {".venv", "venv", "__pycache__", ".git", "node_modules", ".pytest_cache"}

STDLIB = set(getattr(sys, "stdlib_module_names", ()))

def requirement_names(path: Path) -> list[str]:
    if not path.exists():
        return []
    names = []
    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith(("-", "git+", "http")):
            continue
        name = re.split(r"[<>=!~;\[\s]", line, maxsplit=1)[0].lower()
        if name:
            names.append(name)
    return names

def source_files():
    # Include root-level Python files such as graph.py, state.py, models.py.
    for p in ROOT.glob("*.py"):
        if not any(part in EXCLUDE for part in p.parts):
            yield p

    for top in ("api", "agents", "rag", "tools", "evaluation", "tests"):
        root = ROOT / top
        if not root.exists():
            continue
        for p in root.rglob("*.py"):
            if not any(part in EXCLUDE for part in p.parts):
                yield p

def imports_from(path: Path) -> set[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
    except SyntaxError as exc:
        return {f"<SYNTAX_ERROR:{exc}>"}

    result = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            result.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            result.add(node.module.split(".")[0])
    return result

def main():
    files = list(source_files())
    prod = defaultdict(set)
    test = defaultdict(set)

    for path in files:
        rel = path.relative_to(ROOT)
        bucket = test if rel.parts and rel.parts[0] in {"tests", "evaluation"} else prod
        for mod in imports_from(path):
            if mod not in STDLIB and not mod.startswith("<SYNTAX_ERROR:"):
                bucket[mod].add(str(rel))

    import_to_dists = md.packages_distributions()

    req_files = sorted(
        [ROOT / "requirements.txt"]
        + list(ROOT.glob("requirements-*.txt"))
    )

    declared_by_file = {}
    declared_all = set()
    for req in req_files:
        names = requirement_names(req)
        if names:
            declared_by_file[req] = names
            declared_all.update(names)

    print("=== SunSafe AI Dependency Usage Audit v2 ===")
    print(f"Repository: {ROOT}")
    print(f"Python: {sys.version.split()[0]}")
    print(f"Python source files scanned: {len(files)}")
    print()

    print("--- Production/runtime imports ---")
    for mod, locations in sorted(prod.items()):
        dists = sorted(set(x.lower() for x in import_to_dists.get(mod, [])))
        declared = [d for d in dists if d in declared_all]
        if declared:
            status = "DECLARED"
        elif dists:
            status = "INSTALLED_NOT_DECLARED"
        else:
            status = "LOCAL_OR_UNMAPPED"
        print(f"{status:<22} import={mod:<28} dist={','.join(dists) or '-'}")
        print(f"  used in: {', '.join(sorted(locations)[:5])}")
    print()

    print("--- Test/evaluation-only imports ---")
    for mod, locations in sorted(test.items()):
        dists = sorted(set(x.lower() for x in import_to_dists.get(mod, [])))
        print(f"import={mod:<28} dist={','.join(dists) or '-'}")
        print(f"  used in: {', '.join(sorted(locations)[:5])}")
    print()

    print("--- Requirements files ---")
    for req, names in declared_by_file.items():
        print(f"\n[{req.relative_to(ROOT)}]")
        for name in names:
            mapped = sorted(
                m for m, ds in import_to_dists.items()
                if any(d.lower() == name for d in ds)
            )
            runtime_hits = [m for m in mapped if m in prod]
            test_hits = [m for m in mapped if m in test]
            if runtime_hits:
                usage = "RUNTIME"
            elif test_hits:
                usage = "TEST/EVAL"
            else:
                usage = "NO_STATIC_IMPORT"
            print(f"{usage:<16} {name:<30} imports={','.join(runtime_hits + test_hits) or '-'}")
    print()

    print("=== IMPORTANT ===")
    print("NO_STATIC_IMPORT does not prove a dependency is removable.")
    print("Before changing requirements, check dynamic imports, optional extras,")
    print("entry points, framework plugins, and deployment/runtime commands.")
    print("Do not uninstall packages from the current .venv during this audit.")

if __name__ == "__main__":
    main()
