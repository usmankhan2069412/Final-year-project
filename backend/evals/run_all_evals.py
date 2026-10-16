"""
Master Evaluation Suite CLI Runner
Runs all component-level evaluations across the Aina AI RAG pipeline and generates a unified summary report.

Usage:
  python -m evals.run_all_evals --all
  python -m evals.run_all_evals --component router
  python -m evals.run_all_evals --component retrieval
  python -m evals.run_all_evals --component generator
"""

import sys
import time
import argparse
import asyncio
from pathlib import Path

# Ensure UTF-8 output encoding on Windows consoles
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Ensure backend root is on Python path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.core.config import settings
from evals.components.eval_router import evaluate_router
from evals.components.eval_rewriter import evaluate_rewriter
from evals.components.eval_cache import evaluate_semantic_cache
from evals.components.eval_retrieval import evaluate_retrieval
from evals.components.eval_reranker import evaluate_reranker
from evals.components.eval_generator import evaluate_generator
from evals.system.eval_e2e_pipeline import evaluate_e2e_pipeline

REPORTS_DIR = Path(__file__).resolve().parent / "reports"

REPORT_FILENAMES = {
    "1. Intent Classification Router": "eval_router_report.md",
    "2. Contextual Query Rewriter": "eval_rewriter_report.md",
    "3. Semantic Cache & Threshold": "eval_cache_report.md",
    "4. Hybrid Retrieval & RRF Fusion": "eval_retrieval_report.md",
    "5. Hallucination Reranker Guardrail": "eval_reranker_report.md",
    "6. Grounded Generator & Persona": "eval_generator_report.md",
    "7. End-to-End System Pipeline": "eval_e2e_system_report.md",
}


async def main():
    parser = argparse.ArgumentParser(description="Aina AI RAG Evaluation Suite (Component + System Level)")
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all component and system-level evaluation benchmarks sequentially"
    )
    parser.add_argument(
        "--system",
        action="store_true",
        help="Run the End-to-End System-Level Evaluation benchmark"
    )
    parser.add_argument(
        "--component",
        type=str,
        choices=["router", "rewriter", "cache", "retrieval", "reranker", "generator", "system"],
        help="Run a specific component or system evaluation"
    )
    args = parser.parse_args()

    if not args.all and not args.component and not args.system:
        parser.print_help()
        print("\n💡 Examples:")
        print("  python -m evals.run_all_evals --all")
        print("  python -m evals.run_all_evals --system\n")
        return

    print("\n" + "=" * 65)
    print("🌟 AINA AI — RAG EVALUATION SUITE (COMPONENT + E2E SYSTEM)")
    print("=" * 65 + "\n")

    summary_cards = []

    if args.all or args.component == "router":
        res = await evaluate_router()
        acc = res["metrics"]["accuracy"] * 100
        summary_cards.append(("1. Intent Classification Router", f"{acc:.1f}% Accuracy (Macro F1: {res['metrics']['macro_f1']:.2f})", f"{res['avg_latency_ms']:.1f} ms"))

    if args.all or args.component == "rewriter":
        res = await evaluate_rewriter()
        summary_cards.append(("2. Contextual Query Rewriter", f"{res['avg_score'] * 100:.1f}% Quality (Coref: {res['resolution_rate']}%)", f"{res['avg_latency_ms']:.1f} ms"))

    if args.all or args.component == "cache":
        res = evaluate_semantic_cache()
        cfg_th = res.get("configured_threshold", settings.CACHE_SIMILARITY_THRESHOLD)
        cfg_acc = res.get("configured_accuracy", 0.0)
        cache_lat = f"{res.get('avg_latency_ms', 0.0):.2f} ms"
        summary_cards.append(("3. Semantic Cache & Threshold", f"{cfg_acc:.1f}% Guarded Acc @ {cfg_th}", cache_lat))

    if args.all or args.component == "retrieval":
        res = evaluate_retrieval()
        dense_stats = res["summary_table"]["Dense Only"]
        ret_lat = f"{res.get('avg_latency_ms', 0.0):.1f} ms"
        summary_cards.append(("4. Hybrid Retrieval & RRF Fusion", f"Dense Hit@1: {dense_stats['Hit Rate @ 1']} | Recall@3: {dense_stats['Recall @ 3']}", ret_lat))

    if args.all or args.component == "reranker":
        res = await evaluate_reranker()
        summary_cards.append(("5. Hallucination Reranker Guardrail", f"Rejection: {res['distractor_rejection_rate']}% | Fallback Acc: {res['fallback_accuracy']}%", f"{res['avg_latency_ms']:.1f} ms"))

    if args.all or args.component == "generator":
        res = await evaluate_generator()
        summary_cards.append(("6. Grounded Generator & Persona", f"Faithfulness: {res['avg_faithfulness'] * 100:.1f}% | Relevance: {res['avg_relevance'] * 100:.1f}%", f"{res['avg_latency_ms']:.1f} ms"))

    if args.all or args.component == "system" or args.system:
        res = await evaluate_e2e_pipeline()
        summary_cards.append(("7. End-to-End System Pipeline", f"{res['e2e_success_rate']:.1f}% Success (Faithful: {res['avg_faithfulness']:.1f}%)", f"{res['avg_cold_latency_ms']:.1f} ms"))

    print("\n" + "=" * 80)
    print("🏆 MASTER COMPONENT EVALUATION SUMMARY REPORT")
    print("=" * 80)
    print(f"{'Component':<38} | {'Benchmark Performance':<32} | {'Avg Latency':<12}")
    print("-" * 88)
    for name, perf, lat in summary_cards:
        print(f"{name:<38} | {perf:<32} | {lat:<12}")
    print("=" * 88 + "\n")

    # Save Master Markdown Report
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    master_file = REPORTS_DIR / "master_eval_summary.md"
    with open(master_file, "w", encoding="utf-8") as f:
        f.write(f"""# Master RAG Component-Level Evaluation Summary

* **Execution Date:** {time.strftime("%Y-%m-%d %H:%M:%S")}
* **Evaluation Target:** Aina AI Full RAG Pipeline Components

## Components Benchmark Results
| # | Component | Primary Benchmark Performance | Average Latency | Report Link |
| :- | :--- | :--- | :--- | :--- |
""")
        for name, perf, lat in summary_cards:
            report_file = REPORT_FILENAMES.get(name, f"eval_{name.split('. ')[-1].lower().replace(' ', '_')}_report.md")
            f.write(f"| 🎯 | **{name}** | `{perf}` | {lat} | [View Details]({report_file}) |\n")

    print(f"📄 Master Markdown summary saved to: {master_file}\n")


if __name__ == "__main__":
    asyncio.run(main())
