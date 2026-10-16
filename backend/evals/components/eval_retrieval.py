"""
Component Evaluator: Hybrid Search Retrieval & Reciprocal Rank Fusion (RRF)
Evaluates Dense Search vs Sparse Keyword Search vs Hybrid RRF Fusion on HitRate@K, MRR@K, Precision, and Recall.
"""

import sys
import json
import time
import math
import re
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Set, Tuple

# Ensure UTF-8 output encoding on Windows consoles
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Ensure backend root is on Python path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from app.services.embedding import embedding_service
from evals.evaluators.retrieval_metrics import (
    hit_rate_at_k,
    mrr_at_k,
    context_precision_at_k,
    context_recall_at_k
)

DATASET_PATH = Path(__file__).resolve().parent.parent / "datasets" / "retrieval_golden_testset.json"
REPORTS_DIR = Path(__file__).resolve().parent.parent / "reports"


def compute_cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
    dot = np.dot(v1, v2)
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return float(dot / (norm1 * norm2))


def compute_sparse_score(query: str, text: str) -> float:
    """Computes BM25-like lexical overlap score for sparse keyword search simulation."""
    query_tokens = set(re.findall(r"\w+", query.lower()))
    text_tokens = re.findall(r"\w+", text.lower())
    if not query_tokens or not text_tokens:
        return 0.0

    score = 0.0
    for token in query_tokens:
        count = text_tokens.count(token)
        if count > 0:
            # TF weighting with length normalization
            score += (count / (count + 1.2))
    return score


def rrf_fusion(
    dense_ranked_ids: List[str],
    sparse_ranked_ids: List[str],
    k: int = 60
) -> List[str]:
    """Merges dense and sparse ranked lists using Reciprocal Rank Fusion."""
    scores: Dict[str, float] = {}

    for rank, doc_id in enumerate(dense_ranked_ids):
        scores[doc_id] = scores.get(doc_id, 0.0) + (1.0 / (k + rank + 1))

    for rank, doc_id in enumerate(sparse_ranked_ids):
        scores[doc_id] = scores.get(doc_id, 0.0) + (1.0 / (k + rank + 1))

    sorted_docs = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    return [doc_id for doc_id, _ in sorted_docs]


def evaluate_retrieval(
    dataset_path: Path = DATASET_PATH
) -> Dict[str, Any]:
    print("\n=======================================================")
    print("🚀 RUNNING COMPONENT EVAL: HYBRID SEARCH & RRF FUSION")
    print("=======================================================\n")

    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset not found at {dataset_path}")

    with open(dataset_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    corpus = data["corpus"]
    queries = data["queries"]

    print(f"Indexing {len(corpus)} corpus knowledge chunks...")
    corpus_texts = [c["text"] for c in corpus]
    corpus_ids = [c["chunk_id"] for c in corpus]

    # Pre-encode all corpus embeddings
    corpus_embeddings = embedding_service.encode(corpus_texts)

    strategies = ["Dense Only", "Sparse Only", "Hybrid RRF (Ours)"]
    strategy_metrics = {
        s: {
            "hit@1": [],
            "hit@3": [],
            "hit@5": [],
            "mrr@3": [],
            "precision@3": [],
            "recall@3": []
        }
        for s in strategies
    }

    detailed_results = []

    print(f"\nEvaluating {len(queries)} test queries across 3 retrieval strategies...")
    print("-" * 80)

    t_ret_0 = time.perf_counter()
    DENSE_MAX_DISTANCE = 0.55  # settings.RERANK_FALLBACK_SIMILARITY_THRESHOLD

    for q in queries:
        query_text = q["query"]
        ground_truth: Set[str] = set(q["relevant_chunk_ids"])

        # 1. Dense search ranking (with production distance cutoff <= 0.55)
        q_emb = embedding_service.encode([query_text], is_query=True)[0]
        dense_scores = [compute_cosine_similarity(q_emb, c_emb) for c_emb in corpus_embeddings]
        dense_ranked = [
            corpus_ids[idx] for idx in np.argsort(dense_scores)[::-1]
            if (1.0 - dense_scores[idx]) <= DENSE_MAX_DISTANCE
        ]

        # 2. Sparse search ranking
        sparse_scores = [compute_sparse_score(query_text, c_text) for c_text in corpus_texts]
        sparse_ranked = [corpus_ids[idx] for idx in np.argsort(sparse_scores)[::-1] if sparse_scores[idx] > 0]

        # 3. Hybrid RRF fusion ranking
        hybrid_ranked = rrf_fusion(dense_ranked, sparse_ranked, k=60)

        rankings = {
            "Dense Only": dense_ranked,
            "Sparse Only": sparse_ranked,
            "Hybrid RRF (Ours)": hybrid_ranked
        }

        # Calculate metrics for each strategy
        for s_name, ranked in rankings.items():
            strategy_metrics[s_name]["hit@1"].append(hit_rate_at_k(ranked, ground_truth, k=1))
            strategy_metrics[s_name]["hit@3"].append(hit_rate_at_k(ranked, ground_truth, k=3))
            strategy_metrics[s_name]["hit@5"].append(hit_rate_at_k(ranked, ground_truth, k=5))
            strategy_metrics[s_name]["mrr@3"].append(mrr_at_k(ranked, ground_truth, k=3))
            strategy_metrics[s_name]["precision@3"].append(context_precision_at_k(ranked, ground_truth, k=3))
            strategy_metrics[s_name]["recall@3"].append(context_recall_at_k(ranked, ground_truth, k=3))

        top_hybrid = hybrid_ranked[:3]
        is_hit = hit_rate_at_k(hybrid_ranked, ground_truth, k=3) == 1.0

        print(
            f"Query [{q['id']}]: \"{query_text[:45]}...\" | "
            f"Ground Truth: {list(ground_truth)} | Top 1 Hybrid: {top_hybrid[0] if top_hybrid else 'NONE'} | "
            f"{('✅ HIT' if is_hit else '❌ MISS')}"
        )

        detailed_results.append({
            "id": q["id"],
            "query": query_text,
            "type": q.get("query_type", "general"),
            "ground_truth": list(ground_truth),
            "dense_top3": dense_ranked[:3],
            "sparse_top3": sparse_ranked[:3],
            "hybrid_top3": hybrid_ranked[:3],
            "is_hybrid_hit@3": is_hit
        })

    print("-" * 80)

    # Compute Averages
    summary_table = {}
    for s_name in strategies:
        summary_table[s_name] = {
            "Hit Rate @ 1": f"{np.mean(strategy_metrics[s_name]['hit@1']) * 100:.1f}%",
            "Hit Rate @ 3": f"{np.mean(strategy_metrics[s_name]['hit@3']) * 100:.1f}%",
            "Hit Rate @ 5": f"{np.mean(strategy_metrics[s_name]['hit@5']) * 100:.1f}%",
            "MRR @ 3": f"{np.mean(strategy_metrics[s_name]['mrr@3']):.4f}",
            "Precision @ 3": f"{np.mean(strategy_metrics[s_name]['precision@3']):.4f}",
            "Recall @ 3": f"{np.mean(strategy_metrics[s_name]['recall@3']) * 100:.1f}%",
        }

    print("\n📊 ABLATION COMPARISON: DENSE vs SPARSE vs HYBRID RRF:")
    print("-" * 85)
    print(f"{'Strategy':<20} | {'Hit@1':<8} | {'Hit@3':<8} | {'Hit@5':<8} | {'MRR@3':<8} | {'Precision@3':<12} | {'Recall@3':<8}")
    print("-" * 85)
    for s_name, stats in summary_table.items():
        print(
            f"{s_name:<20} | {stats['Hit Rate @ 1']:<8} | {stats['Hit Rate @ 3']:<8} | "
            f"{stats['Hit Rate @ 5']:<8} | {stats['MRR @ 3']:<8} | {stats['Precision @ 3']:<12} | {stats['Recall @ 3']:<8}"
        )
    print("-" * 85)

    # Generate Markdown Report
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_file = REPORTS_DIR / "eval_retrieval_report.md"

    md_content = f"""# Component Evaluation Report: Hybrid Retrieval & RRF Fusion

* **Date:** {time.strftime("%Y-%m-%d %H:%M:%S")}
* **Corpus Chunks Indexed:** {len(corpus)}
* **Total Benchmark Queries:** {len(queries)}

## Strategy Ablation Comparison
| Retrieval Strategy | Hit Rate @ 1 | Hit Rate @ 3 | Hit Rate @ 5 | MRR @ 3 | Precision @ 3 | Recall @ 3 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
"""
    for s_name, stats in summary_table.items():
        md_content += (
            f"| **{s_name}** | {stats['Hit Rate @ 1']} | {stats['Hit Rate @ 3']} | "
            f"{stats['Hit Rate @ 5']} | {stats['MRR @ 3']} | {stats['Precision @ 3']} | {stats['Recall @ 3']} |\n"
        )

    md_content += """
## Detailed Query Retrieval Results
| ID | Query Type | Query Text | Ground Truth | Top 3 Hybrid Retrieved | Hybrid Hit @ 3 |
| :--- | :--- | :--- | :--- | :--- | :--- |
"""
    for r in detailed_results:
        st = "✅ HIT" if r["is_hybrid_hit@3"] else "❌ MISS"
        md_content += (
            f"| {r['id']} | {r['type']} | \"{r['query']}\" | "
            f"`{r['ground_truth']}` | `{r['hybrid_top3']}` | {st} |\n"
        )

    with open(report_file, "w", encoding="utf-8") as f:
        f.write(md_content)

    avg_latency_ms = ((time.perf_counter() - t_ret_0) * 1000) / len(queries) if queries else 0.0
    print(f"\n📄 Full Markdown report saved to: {report_file} (Avg retrieval latency: {avg_latency_ms:.2f} ms)\n")

    return {
        "summary_table": summary_table,
        "detailed_results": detailed_results,
        "avg_latency_ms": round(avg_latency_ms, 2)
    }


if __name__ == "__main__":
    evaluate_retrieval()
