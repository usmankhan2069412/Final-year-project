"""
Classification metrics for Intent Routing and categorical component evaluations.
Includes Accuracy, Precision, Recall, F1-Scores, and Confusion Matrix generators.
"""

from typing import List, Dict, Any, Tuple
from collections import defaultdict


def calculate_classification_metrics(
    y_true: List[str],
    y_pred: List[str],
    labels: List[str]
) -> Dict[str, Any]:
    """
    Computes Accuracy, per-class Precision, Recall, F1-score, Macro F1, and Weighted F1.
    """
    total_samples = len(y_true)
    if total_samples == 0:
        return {
            "accuracy": 0.0,
            "macro_f1": 0.0,
            "weighted_f1": 0.0,
            "per_class": {},
            "total_samples": 0
        }

    correct = sum(1 for yt, yp in zip(y_true, y_pred) if yt == yp)
    accuracy = correct / total_samples

    tp = defaultdict(int)
    fp = defaultdict(int)
    fn = defaultdict(int)
    support = defaultdict(int)

    for yt, yp in zip(y_true, y_pred):
        support[yt] += 1
        if yt == yp:
            tp[yt] += 1
        else:
            fp[yp] += 1
            fn[yt] += 1

    per_class = {}
    f1_list = []
    weighted_f1_sum = 0.0

    for label in labels:
        p = tp[label] / (tp[label] + fp[label]) if (tp[label] + fp[label]) > 0 else 0.0
        r = tp[label] / (tp[label] + fn[label]) if (tp[label] + fn[label]) > 0 else 0.0
        f1 = (2 * p * r) / (p + r) if (p + r) > 0 else 0.0

        class_support = support[label]
        per_class[label] = {
            "precision": round(p, 4),
            "recall": round(r, 4),
            "f1_score": round(f1, 4),
            "support": class_support
        }
        f1_list.append(f1)
        weighted_f1_sum += f1 * class_support

    macro_f1 = sum(f1_list) / len(labels) if labels else 0.0
    weighted_f1 = weighted_f1_sum / total_samples if total_samples > 0 else 0.0

    return {
        "accuracy": round(accuracy, 4),
        "macro_f1": round(macro_f1, 4),
        "weighted_f1": round(weighted_f1, 4),
        "per_class": per_class,
        "total_samples": total_samples
    }


def generate_confusion_matrix(
    y_true: List[str],
    y_pred: List[str],
    labels: List[str]
) -> Tuple[Dict[str, Dict[str, int]], str]:
    """
    Generates a 2D confusion matrix dictionary and a clean ASCII formatted table string.
    Rows: Actual (Ground Truth)
    Cols: Predicted
    """
    matrix: Dict[str, Dict[str, int]] = {
        actual: {pred: 0 for pred in labels} for actual in labels
    }

    for yt, yp in zip(y_true, y_pred):
        if yt in matrix and yp in matrix[yt]:
            matrix[yt][yp] += 1

    # Format ASCII Table
    col_width = max(max((len(l) for l in labels), default=10), 12) + 2
    header = f"{'Actual \\ Pred':<{col_width}}" + "".join(f"{l:<{col_width}}" for l in labels)
    separator = "-" * len(header)
    
    lines = [separator, header, separator]
    for actual in labels:
        row_str = f"{actual:<{col_width}}"
        for pred in labels:
            count = matrix[actual][pred]
            row_str += f"{count:<{col_width}}"
        lines.append(row_str)
    lines.append(separator)

    return matrix, "\n".join(lines)
