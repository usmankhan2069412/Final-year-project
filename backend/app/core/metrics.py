from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

# Define telemetry metrics for Aina AI RAG
chat_requests_total = Counter(
    "aina_chat_requests_total",
    "Total chat requests handled by Aina AI RAG",
    ["intent", "outcome"]
)

chat_latency_seconds = Histogram(
    "aina_chat_latency_seconds",
    "End-to-end chat generation response time in seconds",
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 15.0, 30.0, 60.0, float("inf"))
)

fallback_total = Counter(
    "aina_fallback_total",
    "Total number of times the 'I don't know' fallback was used"
)

embedding_errors_total = Counter(
    "aina_embedding_errors_total",
    "Total number of errors encountered calling the Gemini embedding API"
)

ingestion_job_duration_seconds = Histogram(
    "aina_ingestion_job_duration_seconds",
    "Total time taken to process knowledge source ingestion job in seconds",
    buckets=(1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0, 600.0, float("inf"))
)

queue_depth = Gauge(
    "aina_queue_depth",
    "Number of knowledge jobs in QUEUED status"
)

worker_last_heartbeat_timestamp = Gauge(
    "aina_worker_last_heartbeat_timestamp",
    "Epoch timestamp of the last successful knowledge worker loop iteration"
)

# Intent classification metrics
intent_classification_method = Counter(
    "aina_intent_classification_method_total",
    "How the intent was classified",
    ["method"]  # "keyword_shortcircuit", "llm", "embedding_fallback"
)

intent_classification_latency = Histogram(
    "aina_intent_classification_latency_seconds",
    "Time taken for intent classification",
    buckets=(0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0)
)

memory_summarization_total = Counter(
    "aina_memory_summarization_total",
    "Number of times conversation memory was summarized"
)
