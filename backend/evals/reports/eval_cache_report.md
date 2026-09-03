# Component Evaluation Report: Semantic Cache & Threshold Optimization

* **Date:** 2026-09-03 17:08:45
* **Total Test Pairs:** 8
* **Configured Threshold:** 0.65
* **Optimal Threshold:** 0.6 (Accuracy: 87.50%)

## Threshold Sweep Comparison
| Threshold | True Positives (Hits) | False Positives (Traps Triggered) | Accuracy % |
| :--- | :--- | :--- | :--- |
| **0.6** | 5 | 1 | 87.5% |
| **0.65** | 4 | 0 | 87.5% |
| **0.7** | 3 | 0 | 75.0% |
| **0.75** | 1 | 0 | 50.0% |
| **0.8** | 0 | 0 | 37.5% |
| **0.85** | 0 | 0 | 37.5% |

## Detailed Query Pair Results
| ID | Cached Query | Test Query | Expected | Cosine Sim | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| c_01 | "What is the refund policy of Aina AI?" | "How can I get my money back on Aina AI?" | **HIT** | `0.7745` | Direct semantic paraphrase |
| c_02 | "How do I invite team members to my organization?" | "Where can I add new members to the team?" | **HIT** | `0.6834` | Synonym paraphrase |
| c_03 | "What are the features of the Starter plan?" | "Tell me what is included in the Starter tier." | **HIT** | `0.7376` | Phrasing variation |
| c_04 | "How do I upgrade to the Professional plan?" | "How do I cancel my Professional subscription?" | **MISS** | `0.6373` | False positive trap: Upgrade vs Cancel |
| c_05 | "How to upload PDF documents?" | "How to delete uploaded documents?" | **MISS** | `0.5685` | False positive trap: Upload vs Delete |
| c_06 | "What is the token limit for gpt-4o?" | "What is the token limit for claude-3.5-sonnet?" | **MISS** | `0.5283` | False positive trap: Different entity |
| c_07 | "Aina platform mein document upload karne ka tareeqa kya hai?" | "Aina par files kaise upload karein?" | **HIT** | `0.7357` | Roman Urdu paraphrase |
| c_08 | "Does Aina support WhatsApp integration?" | "How do I integrate my bot with WhatsApp?" | **HIT** | `0.6062` | Inquiry vs Setup question |
