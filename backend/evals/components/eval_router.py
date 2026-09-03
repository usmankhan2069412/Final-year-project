"""
Component Evaluator: Intent Classification Router (SemanticRouter)
Runs the golden testset against SemanticRouter and computes Accuracy, F1-scores, and Confusion Matrix.
"""

import os
import sys
import json
import time
import asyncio
from pathlib import Path
from typing import Dict, Any, List

# Ensure backend root is on Python path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from app.services.semantic_router import SemanticRouter
from evals.evaluators.classification_metrics import (
    calculate_classification_metrics,
    generate_confusion_matrix
)

DATASET_PATH = Path(__file__).resolve().parent.parent / "datasets" / "router_golden_testset.json"
REPORTS_DIR = Path(__file__).resolve().parent.parent / "reports"


async def evaluate_router(
    dataset_path: Path = DATASET_PATH,
    api_key: str = None
) -> Dict[str, Any]:
    print("\n=======================================================")
    print("🚀 RUNNING COMPONENT EVAL: INTENT CLASSIFICATION ROUTER")
    print("=======================================================\n")

    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset not found at {dataset_path}")

    with open(dataset_path, "r", encoding="utf-8") as f:
        test_cases = json.load(f)

    # Initialize router if needed
    SemanticRouter._initialize()

    y_true: List[str] = []
    y_pred: List[str] = []
    latencies: List[float] = []
    detailed_results: List[Dict[str, Any]] = []

    LABELS = [
        "RAG_LOOKUP",
        "CONVERSATIONAL",
        "AGENT_HANDOFF",
        "FRUSTRATION",
        "HISTORY_TRANSFORM"
    ]

    print(f"Loaded {len(test_cases)} test cases from {dataset_path.name}")
    print("-" * 75)
    print(f"{'ID':<6} | {'Language':<10} | {'Expected':<18} | {'Predicted':<18} | {'Status':<6}")
    print("-" * 75)

    for tc in test_cases:
        msg = tc["message"]
        expected = tc["expected_intent"]
        lang = tc.get("language", "unknown")

        effective_api_key = api_key or "managed-by-openrouter"
        t0 = time.monotonic()
        raw_pred = await SemanticRouter.classify(
            message=msg,
            api_key=effective_api_key,
        )
        latency_ms = (time.monotonic() - t0) * 1000
        latencies.append(latency_ms)

        predicted = raw_pred if raw_pred else "RAG_LOOKUP"

        y_true.append(expected)
        y_pred.append(predicted)

        is_match = (expected == predicted)
        status = "✅ PASS" if is_match else "❌ FAIL"

        print(f"{tc['id']:<6} | {lang:<10} | {expected:<18} | {predicted:<18} | {status:<6}")

        detailed_results.append({
            "id": tc["id"],
            "message": msg,
            "language": lang,
            "expected_intent": expected,
            "predicted_intent": predicted,
            "is_correct": is_match,
            "latency_ms": round(latency_ms, 2)
        })

    print("-" * 75)

    # Calculate Metrics
    metrics = calculate_classification_metrics(y_true, y_pred, LABELS)
    matrix_dict, matrix_ascii = generate_confusion_matrix(y_true, y_pred, LABELS)

    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0

    print("\n📊 EVALUATION SUMMARY METRICS:")
    print(f" • Overall Accuracy : {metrics['accuracy'] * 100:.2f}%")
    print(f" • Macro F1-Score   : {metrics['macro_f1']:.4f}")
    print(f" • Weighted F1-Score: {metrics['weighted_f1']:.4f}")
    print(f" • Average Latency  : {avg_latency:.2f} ms\n")

    print("📈 PER-CLASS BREAKDOWN:")
    for label, stats in metrics["per_class"].items():
        print(f" • {label:<18}: Precision={stats['precision']:.2f}, Recall={stats['recall']:.2f}, F1={stats['f1_score']:.2f} (Support={stats['support']})")

    print("\n🔍 CONFUSION MATRIX (Rows: Ground Truth, Cols: Predicted):")
    print(matrix_ascii)

    # Generate Markdown Report
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_file = REPORTS_DIR / "eval_router_report.md"

    md_content = f"""# Component Evaluation Report: Intent Classification Router

* **Date:** {time.strftime("%Y-%m-%d %H:%M:%S")}
* **Total Samples:** {metrics['total_samples']}
* **Overall Accuracy:** {metrics['accuracy'] * 100:.2f}%
* **Macro F1:** {metrics['macro_f1']:.4f}
* **Average Latency:** {avg_latency:.2f} ms

## Per-Class Performance
| Intent | Precision | Recall | F1-Score | Support |
| :--- | :--- | :--- | :--- | :--- |
"""
    for label, stats in metrics["per_class"].items():
        md_content += f"| **{label}** | {stats['precision']:.2f} | {stats['recall']:.2f} | {stats['f1_score']:.2f} | {stats['support']} |\n"

    md_content += f"""
## Confusion Matrix
```
{matrix_ascii}
```

## Detailed Test Case Results
| ID | Language | Message | Expected | Predicted | Status | Latency |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
"""
    for r in detailed_results:
        st = "✅ PASS" if r["is_correct"] else "❌ FAIL"
        md_content += f"| {r['id']} | {r['language']} | {r['message']} | {r['expected_intent']} | {r['predicted_intent']} | {st} | {r['latency_ms']} ms |\n"

    with open(report_file, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"\n📄 Full Markdown report saved to: {report_file}\n")

    return {
        "metrics": metrics,
        "confusion_matrix": matrix_dict,
        "avg_latency_ms": round(avg_latency, 2),
        "detailed_results": detailed_results
    }


if __name__ == "__main__":
    asyncio.run(evaluate_router())
