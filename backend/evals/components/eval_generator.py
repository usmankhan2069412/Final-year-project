"""
Component Evaluator: Grounded Generator & Faithfulness (rag_answer_node)
Runs LLM-as-a-Judge on Faithfulness, Answer Relevance, and Persona Tone Adherence.
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

from app.services.chat import AgentGraphExecutor
from evals.evaluators.judge_llm import LLMJudge

DATASET_PATH = Path(__file__).resolve().parent.parent / "datasets" / "generation_golden_testset.json"
REPORTS_DIR = Path(__file__).resolve().parent.parent / "reports"


async def evaluate_generator(
    dataset_path: Path = DATASET_PATH,
    api_key: str = None
) -> Dict[str, Any]:
    print("\n=======================================================")
    print("🚀 RUNNING COMPONENT EVAL: GENERATOR & FAITHFULNESS")
    print("=======================================================\n")

    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset not found at {dataset_path}")

    with open(dataset_path, "r", encoding="utf-8") as f:
        test_cases = json.load(f)

    effective_api_key = api_key or "managed-by-openrouter"
    judge = LLMJudge(api_key=effective_api_key)

    total_cases = len(test_cases)
    faithfulness_scores = []
    relevance_scores = []
    persona_scores = []
    latencies = []
    detailed_results = []

    print(f"Loaded {total_cases} generation test cases from {dataset_path.name}")
    print("-" * 90)
    print(f"{'ID':<6} | {'Language':<11} | {'Faithfulness':<13} | {'Relevance':<10} | {'Persona Tone':<13} | {'Latency':<8}")
    print("-" * 90)

    for tc in test_cases:
        p_data = tc["persona"]
        mock_persona = SimpleNamespace(
            name=p_data["name"],
            language=p_data["language"],
            fallback="I do not have those details right now.",
            description=p_data.get("description", "")
        )

        state = {
            "user_message": tc["user_message"],
            "rewritten_query": tc["user_message"],
            "context_text": tc["context_text"],
            "is_relevant": True,
            "persona": mock_persona,
            "traits": p_data.get("traits", ["Professional"]),
            "api_key": effective_api_key,
            "model_name": "openai/gpt-4o-mini",
        }

        t0 = time.monotonic()
        gen_output = await AgentGraphExecutor.rag_answer_node(state)
        latency_ms = (time.monotonic() - t0) * 1000
        latencies.append(latency_ms)

        generated_answer = gen_output.get("response", "")

        # 1. Evaluate Faithfulness
        f_res = await judge.evaluate_faithfulness(
            question=tc["user_message"],
            context=tc["context_text"],
            answer=generated_answer
        )
        f_score = float(f_res.get("score", 0.0))
        faithfulness_scores.append(f_score)

        # 2. Evaluate Answer Relevance
        r_res = await judge.evaluate_answer_relevance(
            question=tc["user_message"],
            answer=generated_answer
        )
        r_score = float(r_res.get("score", 0.0))
        relevance_scores.append(r_score)

        # 3. Evaluate Persona Adherence
        p_res = await judge.evaluate_persona_adherence(
            persona_name=p_data["name"],
            persona_traits=p_data.get("traits", []),
            answer=generated_answer
        )
        p_score = float(p_res.get("score", 0.0))
        persona_scores.append(p_score)

        print(
            f"{tc['id']:<6} | {tc.get('language', 'en'):<11} | "
            f"{f_score:<13.2f} | {r_score:<10.2f} | {p_score:<13.2f} | {latency_ms:<8.1f} ms"
        )

        detailed_results.append({
            "id": tc["id"],
            "language": tc.get("language", "en"),
            "user_message": tc["user_message"],
            "context_text": tc["context_text"],
            "generated_answer": generated_answer,
            "ground_truth_answer": tc.get("ground_truth_answer", ""),
            "faithfulness_score": f_score,
            "faithfulness_reasoning": f_res.get("reasoning", ""),
            "relevance_score": r_score,
            "relevance_reasoning": r_res.get("reasoning", ""),
            "persona_score": p_score,
            "persona_reasoning": p_res.get("reasoning", ""),
            "latency_ms": round(latency_ms, 2)
        })

    print("-" * 90)

    avg_f = sum(faithfulness_scores) / len(faithfulness_scores) if faithfulness_scores else 0.0
    avg_r = sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0.0
    avg_p = sum(persona_scores) / len(persona_scores) if persona_scores else 0.0
    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0

    print("\n📊 GENERATION EVALUATION SUMMARY:")
    print(f" • Average Faithfulness (Groundedness) : {avg_f * 100:.2f}% ({avg_f:.2f} / 1.0)")
    print(f" • Average Answer Relevance             : {avg_r * 100:.2f}% ({avg_r:.2f} / 1.0)")
    print(f" • Average Persona Tone Adherence       : {avg_p * 100:.2f}% ({avg_p:.2f} / 1.0)")
    print(f" • Average Generation Latency           : {avg_latency:.2f} ms\n")

    # Generate Markdown Report
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_file = REPORTS_DIR / "eval_generator_report.md"

    md_content = f"""# Component Evaluation Report: Grounded Generator & Faithfulness

* **Date:** {time.strftime("%Y-%m-%d %H:%M:%S")}
* **Total Samples:** {total_cases}
* **Faithfulness Score (Groundedness):** {avg_f * 100:.2f}%
* **Answer Relevance Score:** {avg_r * 100:.2f}%
* **Persona Tone Adherence:** {avg_p * 100:.2f}%
* **Average Latency:** {avg_latency:.2f} ms

## Detailed Generation Results
| ID | Language | Question | Faithfulness | Relevance | Persona | Latency |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
"""
    for r in detailed_results:
        md_content += (
            f"| {r['id']} | {r['language']} | \"{r['user_message']}\" | "
            f"{r['faithfulness_score']:.2f} | {r['relevance_score']:.2f} | "
            f"{r['persona_score']:.2f} | {r['latency_ms']} ms |\n"
        )

    md_content += """
## Sample Answers & Judge Breakdown
"""
    for r in detailed_results:
        md_content += f"""
### Test Case [{r['id']}]: {r['user_message']}
* **Generated Answer:** {r['generated_answer']}
* **Faithfulness:** `{r['faithfulness_score']:.2f}` — _{r['faithfulness_reasoning']}_
* **Relevance:** `{r['relevance_score']:.2f}` — _{r['relevance_reasoning']}_
* **Persona:** `{r['persona_score']:.2f}` — _{r['persona_reasoning']}_
---
"""

    with open(report_file, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"📄 Full Markdown report saved to: {report_file}\n")

    return {
        "avg_faithfulness": round(avg_f, 4),
        "avg_relevance": round(avg_r, 4),
        "avg_persona": round(avg_p, 4),
        "avg_latency_ms": round(avg_latency, 2),
        "detailed_results": detailed_results
    }


if __name__ == "__main__":
    asyncio.run(evaluate_generator())
