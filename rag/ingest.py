"""Official-source ingestion pipeline for WHO/CDC HTML and CDC PDF pages.

Run:
    python -m rag.ingest
    python -m rag.ingest --refresh

The pipeline downloads only URLs declared in knowledge/sources.json, extracts
readable page text, chunks it, and writes knowledge/corpus.json with source
metadata. CDC currently blocks direct requests to several cdc.gov HTML pages
with HTTP 403, so the heat source can use an official CDC Stacks PDF mirror.
"""

from __future__ import annotations

import argparse
import io
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from rag.chunking import chunk_text, normalize_text

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "knowledge" / "sources.json"
CORPUS = ROOT / "knowledge" / "corpus.json"
RAW = ROOT / "knowledge" / "raw"

HEADERS = {
    "User-Agent": "SunSafe-AI/2.0 (+research-demo; contact project owner)",
    "Accept": "text/html,application/xhtml+xml,application/pdf;q=0.9,*/*;q=0.8",
}


def fetch_html(url: str) -> str:
    response = requests.get(url, headers=HEADERS, timeout=20)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg", "nav", "footer"]):
        tag.decompose()

    main = soup.find("main") or soup.find("article") or soup.body or soup
    return normalize_text(main.get_text(" ", strip=True))


def fetch_pdf(url: str) -> str:
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()

    content_type = response.headers.get("content-type", "").lower()
    if "pdf" not in content_type and not url.lower().endswith(".pdf"):
        raise RuntimeError(
            f"Expected PDF response from {url}, "
            f"got content-type={content_type!r}"
        )

    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError(
            "PDF ingestion requires pypdf. Install it with: "
            "python -m pip install pypdf"
        ) from exc

    reader = PdfReader(io.BytesIO(response.content))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    text = normalize_text(text)

    if not text:
        raise RuntimeError(f"No extractable text found in PDF: {url}")

    return text


def fetch_source(source: dict) -> str:
    url = source.get("fetch_url", source["url"])
    fmt = source.get("format", "").lower()

    if fmt == "pdf" or url.lower().endswith(".pdf"):
        return fetch_pdf(url)

    return fetch_html(url)


def ingest(refresh: bool = False) -> list[dict]:
    sources = json.loads(SOURCES.read_text(encoding="utf-8"))

    if not refresh:
        return json.loads(CORPUS.read_text(encoding="utf-8"))

    RAW.mkdir(parents=True, exist_ok=True)

    all_chunks: list[dict] = []
    errors: list[dict] = []
    fetched_at = datetime.now(timezone.utc).isoformat()

    for source in sources:
        try:
            text = fetch_source(source)

            slug = re.sub(
                r"[^a-z0-9]+",
                "_",
                source["source_id"].lower(),
            ).strip("_")

            (RAW / f"{slug}.txt").write_text(
                text,
                encoding="utf-8",
            )

            chunks = chunk_text(text)

            for i, chunk in enumerate(chunks):
                all_chunks.append(
                    {
                        "id": f"{source['source_id']}_{i:04d}",
                        "source_id": source["source_id"],
                        "source": (
                            f"{source['publisher']} — "
                            f"{source['title']}"
                        ),
                        "publisher": source["publisher"],
                        "title": source["title"],
                        "url": source["url"],
                        "topic": source["topic"],
                        "text": chunk,
                        "retrieved_at": fetched_at,
                        "domain": urlparse(source["url"]).netloc,
                    }
                )

        except Exception as exc:
            errors.append(
                {
                    "source": source["url"],
                    "fetch_url": source.get(
                        "fetch_url",
                        source["url"],
                    ),
                    "error": str(exc),
                }
            )

    if not all_chunks:
        raise RuntimeError(
            f"No sources ingested. Errors: {errors}"
        )

    CORPUS.write_text(
        json.dumps(
            all_chunks,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    (RAW / "ingestion_errors.json").write_text(
        json.dumps(
            errors,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    return all_chunks


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Fetch official WHO/CDC pages and rebuild corpus",
    )
    args = parser.parse_args()

    docs = ingest(refresh=args.refresh)

    print(f"Corpus chunks: {len(docs)}")

    if args.refresh:
        print(f"Raw snapshots: {RAW}")

        error_file = RAW / "ingestion_errors.json"
        errors = json.loads(
            error_file.read_text(encoding="utf-8")
        )
        print(f"Ingestion errors: {len(errors)}")


if __name__ == "__main__":
    main()
