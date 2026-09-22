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

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from app.services.semantic_router import SemanticRouter
from evals.evaluators.classification_metrics import (
    calculate_classification_metrics,
    generate_confusion_matrix
)

DATASET_PATH = Path(__file__).resolve().parent.parent / "datasets" / "router_golden_testset.json"
REPORTS_DIR = Path(__file__).resolve().parent.parent / "reports"


class EvalPersona:
    def __init__(self, name: str, description: str, traits: List[str] = None):
        self.name = name
        self.description = description
        self.traits = traits or []


async def evaluate_router(
    dataset_path: Path = DATASET_PATH,
    api_key: str = None
) -> Dict[str, Any]:
    print("\n=======================================================")
    print("RUNNING COMPONENT EVAL: INTENT CLASSIFICATION ROUTER")
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
    confidences: List[float] = []
    detailed_results: List[Dict[str, Any]] = []

    LABELS = [
        "RAG_LOOKUP",
        "CONVERSATIONAL",
        "AGENT_HANDOFF",
        "FRUSTRATION",
        "HISTORY_TRANSFORM"
    ]

    print(f"Loaded {len(test_cases)} test cases from {dataset_path.name}")
    print("-" * 88)
    print(f"{'ID':<6} | {'Language':<10} | {'Expected':<18} | {'Predicted':<18} | {'Method':<12} | {'Conf':<6} | {'Status':<6}")
    print("-" * 88)

    for tc in test_cases:
        msg = tc["message"]
        expected = tc["expected_intent"]
        lang = tc.get("language", "unknown")

        raw_persona = tc.get("persona")
        persona_obj = None
        traits = None
        if raw_persona:
            persona_obj = EvalPersona(
                name=raw_persona.get("name", "Assistant"),
                description=raw_persona.get("description", ""),
                traits=raw_persona.get("traits", [])
            )
            traits = persona_obj.traits

        history = tc.get("history") or []

        effective_api_key = api_key or "managed-by-openrouter"
        t0 = time.monotonic()
        pred, conf, probs, method = await SemanticRouter.classify_with_details(
            message=msg,
            persona=persona_obj,
            traits=traits,
            history=history,
            api_key=effective_api_key,
        )
        latency_ms = (time.monotonic() - t0) * 1000
        latencies.append(latency_ms)
        if conf is not None:
            confidences.append(conf)

        predicted = pred if pred else "RAG_LOOKUP"

        y_true.append(expected)
        y_pred.append(predicted)

        is_match = (expected == predicted)
        status = "PASS" if is_match else "FAIL"

        conf_str = f"{conf:.2f}" if conf is not None else "N/A"
        print(f"{tc['id']:<6} | {lang:<10} | {expected:<18} | {predicted:<18} | {method:<12} | {conf_str:<6} | {status:<6}", flush=True)

        detailed_results.append({
            "id": tc["id"],
            "message": msg,
            "language": lang,
            "expected_intent": expected,
            "predicted_intent": predicted,
            "method": method,
            "confidence": conf,
            "is_correct": is_match,
            "latency_ms": round(latency_ms, 2)
        })

    print("-" * 88)

    # Calculate Metrics
    metrics = calculate_classification_metrics(y_true, y_pred, LABELS)
    matrix_dict, matrix_ascii = generate_confusion_matrix(y_true, y_pred, LABELS)

    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0

    # Confidence Statistics and Distribution Histogram
    valid_confs = [c for c in confidences if c is not None]
    if valid_confs:
        sorted_confs = sorted(valid_confs)
        min_conf = sorted_confs[0]
        max_conf = sorted_confs[-1]
        mean_conf = sum(sorted_confs) / len(sorted_confs)
        p50_conf = sorted_confs[len(sorted_confs) // 2]
        p90_conf = sorted_confs[int(len(sorted_confs) * 0.9)]

        b_0_50 = sum(1 for c in valid_confs if c < 0.50)
        b_50_70 = sum(1 for c in valid_confs if 0.50 <= c < 0.70)
        b_70_90 = sum(1 for c in valid_confs if 0.70 <= c < 0.90)
        b_90_100 = sum(1 for c in valid_confs if c >= 0.90)
    else:
        min_conf = max_conf = mean_conf = p50_conf = p90_conf = 0.0
        b_0_50 = b_50_70 = b_70_90 = b_90_100 = 0

    print("\n📊 EVALUATION SUMMARY METRICS:")
    print(f" • Overall Accuracy : {metrics['accuracy'] * 100:.2f}%")
    print(f" • Macro F1-Score   : {metrics['macro_f1']:.4f}")
    print(f" • Weighted F1-Score: {metrics['weighted_f1']:.4f}")
    print(f" • Average Latency  : {avg_latency:.2f} ms")
    print(f" • Confidence Stats : Min={min_conf:.2f}, Mean={mean_conf:.2f}, P50={p50_conf:.2f}, P90={p90_conf:.2f}, Max={max_conf:.2f}")
    print(f" • Conf Histogram   : [0.0-0.5): {b_0_50}, [0.5-0.7): {b_50_70}, [0.7-0.9): {b_70_90}, [0.9-1.0]: {b_90_100}\n")

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
