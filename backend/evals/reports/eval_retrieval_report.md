# Component Evaluation Report: Hybrid Retrieval & RRF Fusion

* **Date:** 2026-09-03 17:28:10
* **Corpus Chunks Indexed:** 8
* **Total Benchmark Queries:** 8

## Strategy Ablation Comparison
| Retrieval Strategy | Hit Rate @ 1 | Hit Rate @ 3 | Hit Rate @ 5 | MRR @ 3 | Precision @ 3 | Recall @ 3 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Dense Only** | 100.0% | 100.0% | 100.0% | 1.0000 | 0.3333 | 100.0% |
| **Sparse Only** | 100.0% | 100.0% | 100.0% | 1.0000 | 0.3333 | 100.0% |
| **Hybrid RRF (Ours)** | 100.0% | 100.0% | 100.0% | 1.0000 | 0.3333 | 100.0% |

## Detailed Query Retrieval Results
| ID | Query Type | Query Text | Ground Truth | Top 3 Hybrid Retrieved | Hybrid Hit @ 3 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| ret_01 | semantic_dense | "How many days do I have to request a refund?" | `['chunk_01']` | `['chunk_01', 'chunk_08', 'chunk_02']` | ✅ HIT |
| ret_02 | sparse_keyword | "Meta Cloud API v21.0 Verify Token Access Token" | `['chunk_03']` | `['chunk_03', 'chunk_01', 'chunk_07']` | ✅ HIT |
| ret_03 | hybrid | "What is the monthly price and limits of the Starter plan?" | `['chunk_02']` | `['chunk_02', 'chunk_01', 'chunk_03']` | ✅ HIT |
| ret_04 | roman_urdu_hybrid | "PDF aur Word files upload karne ki limit kya hai?" | `['chunk_04']` | `['chunk_04', 'chunk_07', 'chunk_02']` | ✅ HIT |
| ret_05 | semantic_dense | "How are embeddings stored and searched in PostgreSQL?" | `['chunk_05']` | `['chunk_05', 'chunk_07', 'chunk_04']` | ✅ HIT |
| ret_06 | semantic_dense | "What happens when a user wants to talk to a real human agent?" | `['chunk_08']` | `['chunk_08', 'chunk_06', 'chunk_02']` | ✅ HIT |
| ret_07 | sparse_keyword | "PostgreSQL Row-Level Security RLS tenant org_id" | `['chunk_07']` | `['chunk_07', 'chunk_05', 'chunk_08']` | ✅ HIT |
| ret_08 | semantic_dense | "How can I customize the bot's tone and greeting message?" | `['chunk_06']` | `['chunk_06', 'chunk_02', 'chunk_08']` | ✅ HIT |
