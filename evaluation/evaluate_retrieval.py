"""Evaluate Recall@K, MRR and nDCG on the retrieval test set."""
from pathlib import Path
import json, math
from rag.retriever import LocalVectorRetriever

ROOT = Path(__file__).resolve().parents[1]
cases = json.loads((ROOT / "evaluation" / "retrieval_eval.json").read_text(encoding="utf-8"))
retriever = LocalVectorRetriever(top_k=5)

hits = 0
rr_sum = 0.0
ndcg_sum = 0.0
for case in cases:
    results = retriever.retrieve(case["query"], top_k=5)
    expected = set(case["expected_topics"])
    relevant = [i for i, r in enumerate(results) if r.get("topic") in expected]
    hit = bool(relevant)
    hits += int(hit)
    if relevant:
        rr_sum += 1.0 / (relevant[0] + 1)
        dcg = 1.0 / math.log2(relevant[0] + 2)
        ndcg_sum += dcg  # one binary relevance target is sufficient for this smoke benchmark
    print(f"{'PASS' if hit else 'FAIL'} | {case['query']} | rank={relevant[0]+1 if relevant else '-'}")

n = len(cases)
print(f"Recall@5: {hits}/{n} = {hits/n:.2%}")
print(f"MRR: {rr_sum/n:.4f}")
print(f"nDCG@5: {ndcg_sum/n:.4f}")
