# Component Evaluation Report: Contextual Query Rewriter

* **Date:** 2026-09-03 17:21:55
* **Total Samples:** 8
* **Quality Score:** 90.00%
* **Coreference Resolution Rate:** 87.50%
* **Average Latency:** 2065.87 ms

## Detailed Test Case Results
| ID | Language | Type | Original Message | Rewritten Query | Expected Query | Score | Latency |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| rw_01 | en | pronoun_resolution | "Does it support WhatsApp integration?" | "Does the Aina AI Starter plan support WhatsApp integration?" | "Does the Aina AI Starter plan support WhatsApp integration?" | 1.00 | 4984.77 ms |
| rw_02 | roman_urdu | pronoun_resolution | "Is ki monthly price kitni hai?" | "Aina AI Pro plan ki monthly price kitni hai?" | "Aina AI Pro plan ki monthly price kitni hai?" | 1.00 | 2044.86 ms |
| rw_03 | en | pronoun_resolution | "How do I apply for that?" | "How do I apply for a refund?" | "How do I apply for a refund on Aina AI?" | 0.80 | 2475.93 ms |
| rw_04 | en | topic_shift_preservation | "What is the refund policy for annual subscriptions?" | "What is the refund policy for annual subscriptions?" | "What is the refund policy for annual subscriptions?" | 1.00 | 1202.38 ms |
| rw_05 | en | context_expansion | "Can I also upload CSV files?" | "Can I upload CSV files?" | "Can I upload CSV files to Aina AI Knowledge Base?" | 0.70 | 2047.46 ms |
| rw_06 | en | no_history_standalone | "How many members can I invite on the Enterprise tier?" | "How many members can I invite on the Enterprise tier?" | "How many members can I invite on the Enterprise tier?" | 1.00 | 2.37 ms |
| rw_07 | urdu | pronoun_resolution | "اس کے لیے کون سا پلان بہترین رہے گا؟" | "کون سا پلان 5 بوٹس کے لیے بہترین رہے گا؟" | "5 بوٹس کے لیے کون سا پلان بہترین رہے گا؟" | 0.90 | 2431.73 ms |
| rw_08 | en | context_expansion | "What distance metric is used for search?" | "What distance metric is used for search in vector embeddings?" | "What distance metric is used for pgvector embedding search in Aina AI?" | 0.80 | 1337.46 ms |
