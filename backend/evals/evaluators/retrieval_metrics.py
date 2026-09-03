"""
Information Retrieval (IR) Evaluation Metrics for RAG Vector Store, Hybrid Search, and Reranking.
Calculates HitRate@K, MRR@K, Context Precision, Context Recall, and NDCG@K.
"""

import math
from typing import List, Set, Dict, Any, Union


def hit_rate_at_k(
    retrieved_ids: List[Union[str, int]],
    ground_truth_ids: Set[Union[str, int]],
    k: int = 4
) -> float:
    """
    Hit Rate @ K: Returns 1.0 if AT LEAST ONE relevant document is in the top K results, else 0.0.
    """
    top_k = retrieved_ids[:k]
    return 1.0 if any(doc_id in ground_truth_ids for doc_id in top_k) else 0.0


def mrr_at_k(
    retrieved_ids: List[Union[str, int]],
    ground_truth_ids: Set[Union[str, int]],
    k: int = 4
) -> float:
    """
    Mean Reciprocal Rank (MRR) @ K: Calculates 1 / rank of the FIRST relevant item in top K.
    If no relevant item is in top K, returns 0.0.
    """
    top_k = retrieved_ids[:k]
    for rank, doc_id in enumerate(top_k, start=1):
        if doc_id in ground_truth_ids:
            return 1.0 / rank
    return 0.0


def context_precision_at_k(
    retrieved_ids: List[Union[str, int]],
    ground_truth_ids: Set[Union[str, int]],
    k: int = 4
) -> float:
    """
    Context Precision @ K: Ratio of relevant retrieved documents in top K to total documents in top K.
    Precision = (Number of relevant docs in Top K) / K
    """
    top_k = retrieved_ids[:k]
    if not top_k:
        return 0.0
    relevant_in_top_k = sum(1 for doc_id in top_k if doc_id in ground_truth_ids)
    return relevant_in_top_k / len(top_k)


def context_recall_at_k(
    retrieved_ids: List[Union[str, int]],
    ground_truth_ids: Set[Union[str, int]],
    k: int = 4
) -> float:
    """
    Context Recall @ K: Ratio of relevant retrieved documents in top K to TOTAL ground-truth documents.
    Recall = (Number of relevant docs in Top K) / (Total relevant docs)
    """
    if not ground_truth_ids:
        return 1.0
    top_k = retrieved_ids[:k]
    relevant_in_top_k = sum(1 for doc_id in top_k if doc_id in ground_truth_ids)
    return relevant_in_top_k / len(ground_truth_ids)


def ndcg_at_k(
    retrieved_ids: List[Union[str, int]],
    ground_truth_relevance: Dict[Union[str, int], float],
    k: int = 4
) -> float:
    """
    Normalized Discounted Cumulative Gain (NDCG) @ K for graded relevance scores.
    """
    top_k = retrieved_ids[:k]
    if not top_k:
        return 0.0

    # DCG calculation
    dcg = 0.0
    for i, doc_id in enumerate(top_k):
        rel = ground_truth_relevance.get(doc_id, 0.0)
        dcg += (2**rel - 1) / math.log2(i + 2)

    # Ideal DCG calculation
    ideal_rels = sorted(ground_truth_relevance.values(), reverse=True)[:k]
    idcg = sum((2**rel - 1) / math.log2(i + 2) for i, rel in enumerate(ideal_rels))

    return (dcg / idcg) if idcg > 0 else 0.0


def calculate_retrieval_suite(
    retrieved_ids: List[Union[str, int]],
    ground_truth_ids: Set[Union[str, int]],
    k_list: List[int] = [1, 3, 5]
) -> Dict[str, float]:
    """
    Evaluates a single query retrieval against standard k values.
    """
    metrics = {}
    for k in k_list:
        metrics[f"hit_rate@{k}"] = hit_rate_at_k(retrieved_ids, ground_truth_ids, k)
        metrics[f"mrr@{k}"] = mrr_at_k(retrieved_ids, ground_truth_ids, k)
        metrics[f"precision@{k}"] = round(context_precision_at_k(retrieved_ids, ground_truth_ids, k), 4)
        metrics[f"recall@{k}"] = round(context_recall_at_k(retrieved_ids, ground_truth_ids, k), 4)
    return metrics
