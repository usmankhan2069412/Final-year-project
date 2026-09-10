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

# Ensure UTF-8 output encoding on Windows consoles
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Ensure backend root is on Python path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from app.services.embedding import embedding_service
from app.services.semantic_cache import SemanticCacheService
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
    print("🚀 RUNNING COMPONENT EVAL: SEMANTIC CACHE + GUARDRAILS")
    print("=======================================================\n")

    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset not found at {dataset_path}")

    with open(dataset_path, "r", encoding="utf-8") as f:
        test_cases = json.load(f)

    total_cases = len(test_cases)
    print(f"Loaded {total_cases} cache test pairs from {dataset_path.name}")
    print(f"Current Configured Threshold: {settings.CACHE_SIMILARITY_THRESHOLD}")
    print("-" * 105)
    print(f"{'ID':<6} | {'Expected':<8} | {'Cosine Sim':<11} | {'Guardrail Status':<24} | {'Outcome @ Default':<20} | {'Description':<30}")
    print("-" * 105)

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

        # Run Deterministic Guardrail Check
        is_compatible, guard_reason = SemanticCacheService.verify_cache_compatibility(
            tc["cached_query"], tc["test_query"]
        )

        expected = tc["expected_outcome"]
        pred_raw = "HIT" if sim >= settings.CACHE_SIMILARITY_THRESHOLD else "MISS"
        pred_guarded = "HIT" if (sim >= settings.CACHE_SIMILARITY_THRESHOLD and is_compatible) else "MISS"

        is_correct = (expected == pred_guarded)
        if not is_compatible:
            guard_label = "🛡️ REJECTED"
        else:
            guard_label = "✓ COMPATIBLE"

        if is_correct:
            if pred_raw == "HIT" and pred_guarded == "MISS":
                status_label = "MISS ✅ PASS (by Guard)"
            else:
                status_label = f"{pred_guarded} ✅ PASS"
        else:
            status_label = f"{pred_guarded} ❌ FAIL"

        print(
            f"{tc['id']:<6} | {expected:<8} | {sim:<11.4f} | "
            f"{guard_label:<24} | {status_label:<20} | {tc.get('description', '')[:30]:<30}"
        )

        results.append({
            "id": tc["id"],
            "cached_query": tc["cached_query"],
            "test_query": tc["test_query"],
            "expected": expected,
            "similarity": round(sim, 4),
            "is_compatible": is_compatible,
            "guard_reason": guard_reason,
            "pred_raw": pred_raw,
            "pred_guarded": pred_guarded,
            "category": tc.get("category", "general"),
            "difficulty": tc.get("difficulty", "normal"),
            "language": tc.get("language", "en"),
            "description": tc.get("description", "")
        })

    print("-" * 105)

    # Threshold Sweep Analysis (Guardrail Protected)
    print("\n📊 THRESHOLD SWEEP & OPTIMIZATION ANALYSIS (WITH GUARDRAILS):")
    print("-" * 88)
    print(f"{'Threshold':<10} | {'TP (Hits)':<10} | {'FP (Traps)':<11} | {'Precision %':<12} | {'Recall %':<10} | {'Accuracy (Guard)':<18} | {'Raw Acc %':<10}")
    print("-" * 88)

    sweep_stats = {}
    best_thresh = settings.CACHE_SIMILARITY_THRESHOLD
    best_acc = 0.0

    for th in thresholds:
        tp = 0
        fp = 0
        tn = 0
        fn = 0
        raw_correct = 0

        for r in results:
            # Raw prediction without guardrail
            p_raw = "HIT" if r["similarity"] >= th else "MISS"
            if p_raw == r["expected"]:
                raw_correct += 1

            # Guarded prediction
            p_guard = "HIT" if (r["similarity"] >= th and r["is_compatible"]) else "MISS"
            exp = r["expected"]
            if exp == "HIT" and p_guard == "HIT":
                tp += 1
            elif exp == "MISS" and p_guard == "HIT":
                fp += 1
            elif exp == "MISS" and p_guard == "MISS":
                tn += 1
            elif exp == "HIT" and p_guard == "MISS":
                fn += 1

        accuracy = ((tp + tn) / total_cases) * 100 if total_cases > 0 else 0.0
        raw_accuracy = (raw_correct / total_cases) * 100 if total_cases > 0 else 0.0
        precision = (tp / (tp + fp) * 100) if (tp + fp) > 0 else 0.0
        recall = (tp / (tp + fn) * 100) if (tp + fn) > 0 else 0.0

        sweep_stats[str(th)] = {
            "accuracy": round(accuracy, 2),
            "raw_accuracy": round(raw_accuracy, 2),
            "precision": round(precision, 2),
            "recall": round(recall, 2),
            "tp": tp,
            "fp": fp,
            "tn": tn,
            "fn": fn
        }

        if accuracy > best_acc:
            best_acc = accuracy
            best_thresh = th

        print(f"{th:<10.2f} | {tp:<10} | {fp:<11} | {precision:<12.2f}% | {recall:<10.2f}% | {accuracy:<18.2f}% | {raw_accuracy:<10.2f}%")

    print("-" * 88)
    print(f"💡 Recommended Optimal Threshold with Guardrails: {best_thresh} (Accuracy: {best_acc:.2f}%)\n")

    # Category Breakdown Analysis @ Configured Threshold
    configured_th = settings.CACHE_SIMILARITY_THRESHOLD
    categories: Dict[str, Dict[str, Any]] = {}
    for r in results:
        cat = r.get("category", "general")
        if cat not in categories:
            categories[cat] = {
                "total": 0,
                "correct_raw": 0,
                "correct_guarded": 0,
                "traps_blocked": 0,
                "false_positives": 0
            }
        categories[cat]["total"] += 1

        p_raw = "HIT" if r["similarity"] >= configured_th else "MISS"
        p_guarded = "HIT" if (r["similarity"] >= configured_th and r["is_compatible"]) else "MISS"

        if p_raw == r["expected"]:
            categories[cat]["correct_raw"] += 1
        if p_guarded == r["expected"]:
            categories[cat]["correct_guarded"] += 1

        if r["expected"] == "MISS" and p_raw == "HIT" and p_guarded == "MISS":
            categories[cat]["traps_blocked"] += 1
        elif r["expected"] == "MISS" and p_guarded == "HIT":
            categories[cat]["false_positives"] += 1

    print(f"🔬 CATEGORY BREAKDOWN (@ Configured Threshold {configured_th}):")
    print("-" * 85)
    print(f"{'Category':<28} | {'Total':<6} | {'Raw Acc %':<11} | {'Guarded Acc %':<15} | {'Traps Intercepted':<18}")
    print("-" * 85)
    for cat, stats in sorted(categories.items()):
        raw_acc = (stats["correct_raw"] / stats["total"]) * 100 if stats["total"] > 0 else 0.0
        guard_acc = (stats["correct_guarded"] / stats["total"]) * 100 if stats["total"] > 0 else 0.0
        print(f"{cat:<28} | {stats['total']:<6} | {raw_acc:<11.1f}% | {guard_acc:<15.1f}% | {stats['traps_blocked']:<18}")
    print("-" * 85 + "\n")

    # Generate Markdown Report
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_file = REPORTS_DIR / "eval_cache_report.md"

    md_content = f"""# Component Evaluation Report: Semantic Cache & Threshold Optimization (w/ Guardrails)

* **Date:** {time.strftime("%Y-%m-%d %H:%M:%S")}
* **Total Test Pairs:** {total_cases}
* **Configured Threshold:** {configured_th}
* **Optimal Guarded Threshold:** {best_thresh} (Accuracy: {best_acc:.2f}%)

## Threshold Sweep Comparison (Baseline vs Guardrails)
| Threshold | TP (Hits) | FP (Traps) | Precision % | Recall % | Guarded Accuracy % | Raw Accuracy % |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
"""
    for th, st in sweep_stats.items():
        md_content += f"| **{th}** | {st['tp']} | {st['fp']} | {st.get('precision', 0)}% | {st.get('recall', 0)}% | **{st['accuracy']}%** | {st.get('raw_accuracy', 0)}% |\n"

    md_content += f"""
## Category Performance Breakdown (@ Threshold {configured_th})
| Category | Total Pairs | Raw Acc % | Guarded Acc % | Traps Intercepted |
| :--- | :--- | :--- | :--- | :--- |
"""
    for cat, stats in sorted(categories.items()):
        raw_acc = (stats["correct_raw"] / stats["total"]) * 100 if stats["total"] > 0 else 0.0
        guard_acc = (stats["correct_guarded"] / stats["total"]) * 100 if stats["total"] > 0 else 0.0
        md_content += f"| `{cat}` | {stats['total']} | {raw_acc:.1f}% | **{guard_acc:.1f}%** | {stats['traps_blocked']} |\n"

    md_content += """
## Detailed Query Pair Results
| ID | Category | Expected | Cosine Sim | Guardrail Status | Final Outcome | Description |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
"""
    for r in results:
        guard_status = "✓ Compatible" if r["is_compatible"] else f"🛡️ Blocked ({r['guard_reason']})"
        outcome = r["pred_guarded"]
        pass_fail = "✅ PASS" if outcome == r["expected"] else "❌ FAIL"
        md_content += (
            f"| {r['id']} | `{r.get('category', 'general')}` | "
            f"**{r['expected']}** | `{r['similarity']:.4f}` | {guard_status} | {outcome} {pass_fail} | {r['description']} |\n"
        )

    with open(report_file, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"📄 Full Markdown report saved to: {report_file}\n")

    return {
        "sweep_stats": sweep_stats,
        "optimal_threshold": best_thresh,
        "category_stats": categories,
        "results": results
    }


if __name__ == "__main__":
    evaluate_semantic_cache()
