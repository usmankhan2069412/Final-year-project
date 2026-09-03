"""
Component Evaluator: Semantic Cache (Cosine Similarity & Threshold Optimization)
Tests semantic hit precision, false-positive trap resistance, and threshold tuning.
"""

import sys
import json
import time
import numpy as np
from pathlib import Path
from typing import Dict, Any, List

# Ensure backend root is on Python path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from app.services.embedding import embedding_service
from app.core.config import settings

DATASET_PATH = Path(__file__).resolve().parent.parent / "datasets" / "cache_golden_testset.json"
REPORTS_DIR = Path(__file__).resolve().parent.parent / "reports"


def cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
    dot = np.dot(v1, v2)
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return float(dot / (norm1 * norm2))


def evaluate_semantic_cache(
    dataset_path: Path = DATASET_PATH,
    thresholds: List[float] = [0.60, 0.65, 0.70, 0.75, 0.80, 0.85]
) -> Dict[str, Any]:
    print("\n=======================================================")
    print("🚀 RUNNING COMPONENT EVAL: SEMANTIC CACHE & THRESHOLD")
    print("=======================================================\n")

    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset not found at {dataset_path}")

    with open(dataset_path, "r", encoding="utf-8") as f:
        test_cases = json.load(f)

    total_cases = len(test_cases)
    print(f"Loaded {total_cases} cache test pairs from {dataset_path.name}")
    print(f"Current Configured Threshold: {settings.CACHE_SIMILARITY_THRESHOLD}")
    print("-" * 90)
    print(f"{'ID':<6} | {'Expected':<8} | {'Cosine Sim':<11} | {'Status @ Default':<18} | {'Description':<35}")
    print("-" * 90)

    cached_texts = [tc["cached_query"] for tc in test_cases]
    test_texts = [tc["test_query"] for tc in test_cases]

    # Batch encode queries
    cached_vecs = embedding_service.encode(cached_texts)
    test_vecs = embedding_service.encode(test_texts)

    results = []
    similarities = []

    for i, tc in enumerate(test_cases):
        sim = cosine_similarity(cached_vecs[i], test_vecs[i])
        similarities.append(sim)

        expected = tc["expected_outcome"]
        predicted = "HIT" if sim >= settings.CACHE_SIMILARITY_THRESHOLD else "MISS"
        is_correct = (expected == predicted)
        status = "✅ PASS" if is_correct else "❌ FAIL"

        print(
            f"{tc['id']:<6} | {expected:<8} | {sim:<11.4f} | "
            f"{(predicted + ' ' + status):<18} | {tc.get('description', ''):<35}"
        )

        results.append({
            "id": tc["id"],
            "cached_query": tc["cached_query"],
            "test_query": tc["test_query"],
            "expected": expected,
            "similarity": round(sim, 4),
            "description": tc.get("description", "")
        })

    print("-" * 90)

    # Threshold Sweep Analysis
    print("\n📊 THRESHOLD SWEEP & OPTIMIZATION ANALYSIS:")
    print("-" * 65)
    print(f"{'Threshold':<12} | {'True Positives':<16} | {'False Positives':<16} | {'Accuracy %':<12}")
    print("-" * 65)

    sweep_stats = {}
    best_thresh = settings.CACHE_SIMILARITY_THRESHOLD
    best_acc = 0.0

    for th in thresholds:
        tp = 0
        fp = 0
        tn = 0
        fn = 0
        for r in results:
            pred = "HIT" if r["similarity"] >= th else "MISS"
            exp = r["expected"]
            if exp == "HIT" and pred == "HIT":
                tp += 1
            elif exp == "MISS" and pred == "HIT":
                fp += 1
            elif exp == "MISS" and pred == "MISS":
                tn += 1
            elif exp == "HIT" and pred == "MISS":
                fn += 1

        accuracy = ((tp + tn) / total_cases) * 100 if total_cases > 0 else 0.0
        sweep_stats[str(th)] = {
            "accuracy": round(accuracy, 2),
            "tp": tp,
            "fp": fp,
            "tn": tn,
            "fn": fn
        }

        if accuracy > best_acc:
            best_acc = accuracy
            best_thresh = th

        print(f"{th:<12.2f} | {tp:<16} | {fp:<16} | {accuracy:<12.2f}%")

    print("-" * 65)
    print(f"💡 Recommended Optimal Threshold: {best_thresh} (Accuracy: {best_acc:.2f}%)\n")

    # Generate Markdown Report
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_file = REPORTS_DIR / "eval_cache_report.md"

    md_content = f"""# Component Evaluation Report: Semantic Cache & Threshold Optimization

* **Date:** {time.strftime("%Y-%m-%d %H:%M:%S")}
* **Total Test Pairs:** {total_cases}
* **Configured Threshold:** {settings.CACHE_SIMILARITY_THRESHOLD}
* **Optimal Threshold:** {best_thresh} (Accuracy: {best_acc:.2f}%)

## Threshold Sweep Comparison
| Threshold | True Positives (Hits) | False Positives (Traps Triggered) | Accuracy % |
| :--- | :--- | :--- | :--- |
"""
    for th, st in sweep_stats.items():
        md_content += f"| **{th}** | {st['tp']} | {st['fp']} | {st['accuracy']}% |\n"

    md_content += """
## Detailed Query Pair Results
| ID | Cached Query | Test Query | Expected | Cosine Sim | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
"""
    for r in results:
        md_content += (
            f"| {r['id']} | \"{r['cached_query']}\" | \"{r['test_query']}\" | "
            f"**{r['expected']}** | `{r['similarity']:.4f}` | {r['description']} |\n"
        )

    with open(report_file, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"📄 Full Markdown report saved to: {report_file}\n")

    return {
        "sweep_stats": sweep_stats,
        "optimal_threshold": best_thresh,
        "results": results
    }


if __name__ == "__main__":
    evaluate_semantic_cache()
