# Component Evaluation Report: Hallucination Reranker & Guardrail

* **Date:** 2026-09-26 15:57:35
* **Total Test Cases:** 30
* **Distractor Rejection Rate:** 44.44%
* **Relevant Chunk Retention Rate:** 100.00%
* **Safe Fallback Accuracy:** 96.67%
* **Average Latency:** 502.86 ms

## Detailed Guardrail Test Results
| ID | Query | Expected State | Actual State | Chunks Kept | Latency | Description |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| rr_01 | "How many days do I have to request a refund?" | Answerable | Answerable | 1/3 | 1731.74 ms | Single relevant chunk mixed with 2 distractors |
| rr_02 | "What are the limitations of the Starter tier?" | Answerable | Answerable | 2/2 | 411.73 ms | Starter query with Enterprise distractor |
| rr_03 | "What is the capital city of France?" | Safe Fallback | Safe Fallback | 0/2 | 397.26 ms | Out-of-scope question: 100% distractors, must trigger safe fallback |
| rr_04 | "Aina platform mein PDF file kaise upload hoti hai?" | Answerable | Answerable | 1/2 | 511.95 ms | Roman Urdu upload query with unrelated SMTP distractor |
| rr_05 | "Who won the cricket world cup in 1992?" | Safe Fallback | Safe Fallback | 0/1 | 696.3 ms | Irrelevant general knowledge query: must trigger safe fallback |
| rr_06 | "What tokens are required to connect WhatsApp using Meta Cloud API v21.0?" | Answerable | Answerable | 1/2 | 699.81 ms | WhatsApp token query with Telegram distractor |
| rr_07 | "What is the maximum single file upload size?" | Answerable | Answerable | 3/3 | 653.89 ms | Numeric limit query with near-miss distractors |
| rr_08 | "Which embedding model and dimensions does Aina AI use?" | Answerable | Answerable | 2/2 | 429.04 ms | Embedding model query with OpenAI distractor |
| rr_09 | "How can I customize the bot's tone and greeting message?" | Answerable | Answerable | 2/2 | 400.64 ms | Persona query with UI theme distractor |
| rr_10 | "How does Aina AI isolate data between different organizations?" | Answerable | Answerable | 1/2 | 415.84 ms | Multi-tenancy security query with contradicting distractor |
| rr_11 | "What happens when a user asks to speak with a human agent?" | Answerable | Answerable | 1/2 | 458.5 ms | Human escalation query with wrong routing distractor |
| rr_12 | "What is the refund policy for Enterprise contracts?" | Answerable | Answerable | 2/2 | 391.14 ms | Enterprise refund query with generic refund distractor |
| rr_13 | "What is the price and chatbot limit of the Professional plan?" | Answerable | Answerable | 2/2 | 461.4 ms | Professional plan query with Starter distractor |
| rr_14 | "How does hybrid search work in the vector database?" | Answerable | Answerable | 2/2 | 414.11 ms | Hybrid search query with contradicting distractor |
| rr_15 | "Which file formats does Aina AI support for document ingestion?" | Answerable | Answerable | 2/2 | 432.17 ms | Supported formats query with restrictive distractor |
| rr_16 | "Refund ke liye kitne din hain?" | Answerable | Answerable | 2/2 | 403.97 ms | Roman Urdu refund query with wrong number distractor |
| rr_17 | "What is the weather in Lahore today?" | Safe Fallback | Safe Fallback | 0/2 | 416.74 ms | Out-of-scope weather query: must trigger safe fallback |
| rr_18 | "Compare the limits of Starter and Professional plans." | Answerable | Answerable | 2/3 | 647.34 ms | Multi-relevant comparison query with Enterprise distractor |
| rr_19 | "How many API requests are allowed for a full refund?" | Answerable | Answerable | 2/2 | 406.04 ms | API request limit query with contradicting distractor |
| rr_20 | "WhatsApp connect karne ke liye kaunse tokens chahiye?" | Answerable | Answerable | 2/2 | 398.14 ms | Roman Urdu WhatsApp token query with incomplete distractor |
| rr_21 | "Who is the CEO of Aina AI?" | Safe Fallback | Answerable | 1/2 | 417.31 ms | Out-of-scope leadership query: must trigger safe fallback |
| rr_22 | "Which library is used to extract PDF text?" | Answerable | Answerable | 2/2 | 412.36 ms | PDF extraction library query with OCR distractor |
| rr_23 | "What is a fallback message in Persona configuration?" | Answerable | Answerable | 2/2 | 418.58 ms | Persona fallback query with error log distractor |
| rr_24 | "How does Aina AI prevent data leaks across tenants?" | Answerable | Answerable | 2/2 | 400.45 ms | Data leak prevention query with contradicting distractor |
| rr_25 | "What technology is used for live handoff to administrators?" | Answerable | Answerable | 2/2 | 395.87 ms | Live handoff technology query with WebSocket distractor |
| rr_26 | "Starter plan ki price kya hai?" | Answerable | Answerable | 2/2 | 404.47 ms | Roman Urdu Starter price query with Professional distractor |
| rr_27 | "What is the best restaurant in Lahore?" | Safe Fallback | Safe Fallback | 0/2 | 406.53 ms | Out-of-scope local recommendation query: must trigger safe fallback |
| rr_28 | "What is the refund window and Starter plan price?" | Answerable | Answerable | 2/3 | 521.01 ms | Multi-relevant refund + pricing query with office hours distractor |
| rr_29 | "Which PostgreSQL extension is used for vector storage?" | Answerable | Answerable | 2/2 | 498.26 ms | Vector extension query with Pinecone distractor |
| rr_30 | "How many team members are allowed on the Professional plan?" | Answerable | Answerable | 2/2 | 433.13 ms | Professional team member limit query with Starter distractor |
