"""Build the persistent Phase-3 RAG index.

Use --refresh to ingest fresh WHO/CDC pages before indexing.
"""
import argparse
from rag.ingest import ingest
from rag.retriever import LocalVectorRetriever

parser = argparse.ArgumentParser()
parser.add_argument("--refresh", action="store_true")
args = parser.parse_args()

ingest(refresh=args.refresh)
r = LocalVectorRetriever(top_k=4)
print(f"Indexed {len(r.documents)} chunks")
print(f"Embedding backend: {r.embedder.backend}")
print(f"Vector DB: SQLite persistent store")
print(f"Index: {r.store.path}")
