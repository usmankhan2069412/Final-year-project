# Component Evaluation Report: Hallucination Reranker & Guardrail

* **Date:** 2026-09-03 17:29:05
* **Total Test Cases:** 5
* **Distractor Rejection Rate:** 85.71%
* **Relevant Chunk Retention Rate:** 100.00%
* **Safe Fallback Accuracy:** 100.00%
* **Average Latency:** 1945.20 ms

## Detailed Guardrail Test Results
| ID | Query | Expected State | Actual State | Chunks Kept | Latency | Description |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| rr_01 | "How many days do I have to request a refund?" | Answerable | Answerable | 1/3 | 2177.49 ms | Single relevant chunk mixed with 2 distractors |
| rr_02 | "What are the limitations of the Starter tier?" | Answerable | Answerable | 2/2 | 1907.98 ms | Starter query with Enterprise distractor |
| rr_03 | "What is the capital city of France?" | Safe Fallback | Safe Fallback | 0/2 | 1816.23 ms | Out-of-scope question: 100% distractors, must trigger safe fallback |
| rr_04 | "Aina platform mein PDF file kaise upload hoti hai?" | Answerable | Answerable | 1/2 | 2159.65 ms | Roman Urdu upload query with unrelated SMTP distractor |
| rr_05 | "Who won the cricket world cup in 1992?" | Safe Fallback | Safe Fallback | 0/1 | 1664.66 ms | Irrelevant general knowledge query: must trigger safe fallback |
