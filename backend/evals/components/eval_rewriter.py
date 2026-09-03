"""
Component Evaluator: Contextual Query Rewriter (rewrite_node)
Tests pronoun resolution, context expansion, and standalone query preservation across multi-turn history.
"""

import sys
import json
import time
import asyncio
from pathlib import Path
from types import SimpleNamespace
from typing import Dict, Any, List

# Ensure backend root is on Python path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from app.models.conversation import MessageRole
from app.services.chat import AgentGraphExecutor
from evals.evaluators.judge_llm import LLMJudge

DATASET_PATH = Path(__file__).resolve().parent.parent / "datasets" / "rewriter_golden_testset.json"
REPORTS_DIR = Path(__file__).resolve().parent.parent / "reports"


async def evaluate_rewriter(
    dataset_path: Path = DATASET_PATH,
    api_key: str = None
) -> Dict[str, Any]:
    print("\n=======================================================")
    print("🚀 RUNNING COMPONENT EVAL: CONTEXTUAL QUERY REWRITER")
    print("=======================================================\n")

    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset not found at {dataset_path}")

    with open(dataset_path, "r", encoding="utf-8") as f:
        test_cases = json.load(f)

    effective_api_key = api_key or "managed-by-openrouter"
    judge = LLMJudge(api_key=effective_api_key)

    total_cases = len(test_cases)
    scores = []
    latencies = []
    detailed_results = []
    coreference_success = 0

    print(f"Loaded {total_cases} test cases from {dataset_path.name}")
    print("-" * 85)
    print(f"{'ID':<6} | {'Language':<10} | {'Test Type':<25} | {'Score':<6} | {'Coreference':<11} | {'Latency':<8}")
    print("-" * 85)

    for tc in test_cases:
        history_objs = [
            SimpleNamespace(
                role=MessageRole.USER if h["role"] == "USER" else MessageRole.BOT,
                content=h["content"]
            )
            for h in tc.get("history", [])
        ]

        history_str = "\n".join([f"{h['role']}: {h['content']}" for h in tc.get("history", [])])

        state = {
            "user_message": tc["user_message"],
            "history": history_objs,
            "api_key": effective_api_key,
            "model_name": "openai/gpt-4o-mini",
        }

        t0 = time.monotonic()
        rewrite_output = await AgentGraphExecutor.rewrite_node(state)
        latency_ms = (time.monotonic() - t0) * 1000
        latencies.append(latency_ms)

        rewritten = rewrite_output.get("rewritten_query", tc["user_message"])

        # LLM-as-a-Judge evaluation
        judge_res = await judge.evaluate_query_rewriter(
            chat_history=history_str,
            user_message=tc["user_message"],
            rewritten_query=rewritten,
            expected_query=tc["expected_standalone_query"]
        )

        score = float(judge_res.get("score", 0.0))
        scores.append(score)
        is_coref = bool(judge_res.get("coreference_resolved", False))
        if is_coref or tc["test_type"] == "no_history_standalone":
            coreference_success += 1

        print(
            f"{tc['id']:<6} | {tc.get('language', 'en'):<10} | "
            f"{tc.get('test_type', ''):<25} | {score:<6.2f} | "
            f"{('YES' if is_coref else 'NO'):<11} | {latency_ms:<8.1f} ms"
        )

        detailed_results.append({
            "id": tc["id"],
            "language": tc.get("language", "en"),
            "test_type": tc.get("test_type", ""),
            "user_message": tc["user_message"],
            "rewritten_query": rewritten,
            "expected_query": tc["expected_standalone_query"],
            "score": score,
            "coreference_resolved": is_coref,
            "hallucination_detected": judge_res.get("hallucination_detected", False),
            "reasoning": judge_res.get("reasoning", ""),
            "latency_ms": round(latency_ms, 2)
        })

    print("-" * 85)

    avg_score = sum(scores) / len(scores) if scores else 0.0
    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
    resolution_rate = (coreference_success / total_cases) * 100 if total_cases > 0 else 0.0

    print("\n📊 EVALUATION SUMMARY METRICS:")
    print(f" • Average Rewriter Quality Score: {avg_score * 100:.2f}% ({avg_score:.2f} / 1.0)")
    print(f" • Coreference Resolution Rate   : {resolution_rate:.2f}%")
    print(f" • Average Rewrite Latency       : {avg_latency:.2f} ms\n")

    # Generate Markdown Report
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_file = REPORTS_DIR / "eval_rewriter_report.md"

    md_content = f"""# Component Evaluation Report: Contextual Query Rewriter

* **Date:** {time.strftime("%Y-%m-%d %H:%M:%S")}
* **Total Samples:** {total_cases}
* **Quality Score:** {avg_score * 100:.2f}%
* **Coreference Resolution Rate:** {resolution_rate:.2f}%
* **Average Latency:** {avg_latency:.2f} ms

## Detailed Test Case Results
| ID | Language | Type | Original Message | Rewritten Query | Expected Query | Score | Latency |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
"""
    for r in detailed_results:
        md_content += (
            f"| {r['id']} | {r['language']} | {r['test_type']} | "
            f"\"{r['user_message']}\" | \"{r['rewritten_query']}\" | "
            f"\"{r['expected_query']}\" | {r['score']:.2f} | {r['latency_ms']} ms |\n"
        )

    with open(report_file, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"📄 Full Markdown report saved to: {report_file}\n")

    return {
        "avg_score": round(avg_score, 4),
        "resolution_rate": round(resolution_rate, 2),
        "avg_latency_ms": round(avg_latency, 2),
        "detailed_results": detailed_results
    }


if __name__ == "__main__":
    asyncio.run(evaluate_rewriter())
