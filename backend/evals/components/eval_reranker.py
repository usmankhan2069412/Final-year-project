"""
Component Evaluator: Hallucination Reranker & Guardrail (validate_node)
Tests cross-encoder reranking, distractor chunk rejection, and safe fallback triggers.
"""

import sys
import json
import time
import asyncio
from pathlib import Path
from typing import Dict, Any, List

# Ensure backend root is on Python path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from app.services.chat import AgentGraphExecutor
from app.core.config import settings

DATASET_PATH = Path(__file__).resolve().parent.parent / "datasets" / "reranker_golden_testset.json"
REPORTS_DIR = Path(__file__).resolve().parent.parent / "reports"


async def evaluate_reranker(
    dataset_path: Path = DATASET_PATH
) -> Dict[str, Any]:
    print("\n=======================================================")
    print("🚀 RUNNING COMPONENT EVAL: RERANKER & GUARDRAIL")
    print("=======================================================\n")

    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset not found at {dataset_path}")

    with open(dataset_path, "r", encoding="utf-8") as f:
        test_cases = json.load(f)

    total_cases = len(test_cases)
    total_distractors = 0
    distractors_rejected = 0
    total_relevant = 0
    relevant_retained = 0
    fallback_correct = 0

    latencies = []
    detailed_results = []

    print(f"Loaded {total_cases} test cases from {dataset_path.name}")
    print(f"Rerank Score Threshold: {settings.RERANK_THRESHOLD}")
    print("-" * 85)
    print(f"{'ID':<6} | {'Expected Fallback?':<20} | {'Actual Relevant?':<18} | {'Chunks Kept':<14} | {'Latency':<8}")
    print("-" * 85)

    for tc in test_cases:
        sources = [
            {"chunk_id": c["chunk_id"], "text": c["text"], "source_id": f"src_{c['chunk_id']}"}
            for c in tc["chunks"]
        ]

        state = {
            "user_message": tc["query"],
            "rewritten_query": tc["query"],
            "sources": sources,
        }

        t0 = time.monotonic()
        res = await AgentGraphExecutor.validate_node(state)
        latency_ms = (time.monotonic() - t0) * 1000
        latencies.append(latency_ms)

        is_relevant = bool(res.get("is_relevant", False))
        kept_sources = res.get("sources", [])
        kept_chunk_ids = {s["chunk_id"] for s in kept_sources}

        # Compute chunk-level ground truth matching
        for c in tc["chunks"]:
            cid = c["chunk_id"]
            should_keep = c["expected_keep"]
            actually_kept = (cid in kept_chunk_ids)

            if not should_keep:
                total_distractors += 1
                if not actually_kept:
                    distractors_rejected += 1
            else:
                total_relevant += 1
                if actually_kept:
                    relevant_retained += 1

        # Check overall fallback correctness
        expected_relevant = tc["expected_is_relevant"]
        is_fallback_match = (is_relevant == expected_relevant)
        if is_fallback_match:
            fallback_correct += 1

        print(
            f"{tc['id']:<6} | {('YES (Out of Scope)' if not expected_relevant else 'NO (Answerable)'):<20} | "
            f"{('YES' if is_relevant else 'NO (Fallback)'):<18} | "
            f"{f'{len(kept_sources)}/{len(sources)} kept':<14} | {latency_ms:<8.1f} ms"
        )

        detailed_results.append({
            "id": tc["id"],
            "query": tc["query"],
            "expected_is_relevant": expected_relevant,
            "actual_is_relevant": is_relevant,
            "total_chunks": len(sources),
            "kept_chunks": len(kept_sources),
            "kept_chunk_ids": list(kept_chunk_ids),
            "description": tc.get("description", ""),
            "latency_ms": round(latency_ms, 2)
        })

    print("-" * 85)

    distractor_rejection_rate = (distractors_rejected / total_distractors * 100) if total_distractors > 0 else 100.0
    relevant_retention_rate = (relevant_retained / total_relevant * 100) if total_relevant > 0 else 100.0
    fallback_accuracy = (fallback_correct / total_cases * 100) if total_cases > 0 else 100.0
    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0

    print("\n📊 EVALUATION SUMMARY METRICS:")
    print(f" • Distractor Rejection Rate : {distractor_rejection_rate:.2f}% ({distractors_rejected}/{total_distractors} distractors dropped)")
    print(f" • Relevant Retention Rate   : {relevant_retention_rate:.2f}% ({relevant_retained}/{total_relevant} valid chunks kept)")
    print(f" • Safe Fallback Accuracy    : {fallback_accuracy:.2f}%")
    print(f" • Average Reranking Latency : {avg_latency:.2f} ms\n")

    # Generate Markdown Report
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_file = REPORTS_DIR / "eval_reranker_report.md"

    md_content = f"""# Component Evaluation Report: Hallucination Reranker & Guardrail

* **Date:** {time.strftime("%Y-%m-%d %H:%M:%S")}
* **Total Test Cases:** {total_cases}
* **Distractor Rejection Rate:** {distractor_rejection_rate:.2f}%
* **Relevant Chunk Retention Rate:** {relevant_retention_rate:.2f}%
* **Safe Fallback Accuracy:** {fallback_accuracy:.2f}%
* **Average Latency:** {avg_latency:.2f} ms

## Detailed Guardrail Test Results
| ID | Query | Expected State | Actual State | Chunks Kept | Latency | Description |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
"""
    for r in detailed_results:
        exp_str = "Answerable" if r["expected_is_relevant"] else "Safe Fallback"
        act_str = "Answerable" if r["actual_is_relevant"] else "Safe Fallback"
        md_content += (
            f"| {r['id']} | \"{r['query']}\" | {exp_str} | {act_str} | "
            f"{r['kept_chunks']}/{r['total_chunks']} | {r['latency_ms']} ms | {r['description']} |\n"
        )

    with open(report_file, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"📄 Full Markdown report saved to: {report_file}\n")

    return {
        "distractor_rejection_rate": round(distractor_rejection_rate, 2),
        "relevant_retention_rate": round(relevant_retention_rate, 2),
        "fallback_accuracy": round(fallback_accuracy, 2),
        "avg_latency_ms": round(avg_latency, 2),
        "detailed_results": detailed_results
    }


if __name__ == "__main__":
    asyncio.run(evaluate_reranker())
