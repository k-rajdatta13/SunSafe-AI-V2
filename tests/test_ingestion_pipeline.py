from rag.chunking import chunk_text
from rag.ingest import fetch_source


def test_chunking_respects_bounds():
    text = "Sentence one. " * 100
    chunks = chunk_text(text, chunk_size=120, overlap=20)
    assert chunks
    assert all(len(c) <= 160 for c in chunks)


def test_source_registry_is_official():
    import json
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    sources = json.loads((root / "knowledge" / "sources.json").read_text())
    assert sources
    assert all(s["publisher"] in {"WHO", "CDC"} for s in sources)
    assert all(s["url"].startswith("https://") for s in sources)
