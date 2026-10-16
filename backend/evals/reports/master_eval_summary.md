# Master RAG Component-Level Evaluation Summary

* **Evaluation Target:** Aina AI Full RAG Pipeline Components

## Components Benchmark Results
| # | Component | Primary Benchmark Performance | Average Latency | Report Link |
| :- | :--- | :--- | :--- | :--- |
| 🎯 | **1. Intent Classification Router** | `98.08% Accuracy (Macro F1: 0.98)` | 423.6 ms | [View Details](eval_router_report.md) |
| 🎯 | **2. Contextual Query Rewriter** | `90.00% Quality (Coref: 87.5%)` | 2065.9 ms | [View Details](eval_rewriter_report.md) |
| 🎯 | **3. Semantic Cache & Threshold** | `97.22% Guarded Acc @ 0.60 (66.67% @ 0.90)` | 0.29 ms | [View Details](eval_cache_report.md) |
| 🎯 | **4. Hybrid Retrieval & RRF Fusion** | `Dense Hit@1: 82.4% | Hit@3: 100.0% | Recall@3: 98.0%` | 2610.5 ms | [View Details](eval_retrieval_report.md) |
| 🎯 | **5. Hallucination Reranker Guardrail** | `Rejection: 44.44% | Fallback Acc: 96.67%` | 502.9 ms | [View Details](eval_reranker_report.md) |
| 🎯 | **6. Grounded Generator & Persona** | `Faithfulness: 100.0% | Relevance: 97.5%` | 2480.7 ms | [View Details](eval_generator_report.md) |
| 🎯 | **7. End-to-End System Pipeline** | `Success: 100.0% | Faithfulness: 92.0%` | 18188.6 ms | [View Details](eval_e2e_system_report.md) |
