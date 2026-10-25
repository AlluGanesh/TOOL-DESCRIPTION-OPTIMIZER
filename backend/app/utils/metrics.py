"""Metrics calculation utilities for tool-selection accuracy, precision, recall, and confusion matrix."""

from typing import Dict, List, Tuple
from backend.app.core.constants import ALL_LABELS
from backend.app.models.evaluation_models import PerToolMetrics

def calculate_accuracy(correct_count: int, total_count: int) -> float:
    """Calculates accuracy ratio safely avoiding division by zero."""
    if total_count <= 0:
        return 0.0
    return round(correct_count / total_count, 4)

def build_confusion_matrix(
    expected_list: List[str],
    predicted_list: List[str],
    labels: List[str] = ALL_LABELS,
) -> Dict[str, Dict[str, int]]:
    """Initializes and builds an exact-match confusion matrix: expected (row) -> predicted (column) -> count.
    
    Guarantees:
    - Stable ordering matching labels parameter.
    - Zero-count cells explicitly initialized and preserved.
    - All 11 classes (10 tools + 'none') included.
    """
    matrix: Dict[str, Dict[str, int]] = {
        expected: {pred: 0 for pred in labels} for expected in labels
    }
    for expected, predicted in zip(expected_list, predicted_list):
        if expected in matrix and predicted in matrix[expected]:
            matrix[expected][predicted] += 1
        elif expected in matrix:
            # If an unexpected prediction occurs, preserve in matrix if label exists
            matrix[expected].setdefault(predicted, 0)
            matrix[expected][predicted] += 1
    return matrix

def calculate_per_tool_metrics(
    expected_list: List[str],
    predicted_list: List[str],
    labels: List[str] = ALL_LABELS,
) -> Dict[str, PerToolMetrics]:
    """Calculates Precision, Recall, F1, and raw counts for every class in the label space."""
    metrics: Dict[str, PerToolMetrics] = {}

    for label in labels:
        tp = sum(1 for exp, pred in zip(expected_list, predicted_list) if exp == label and pred == label)
        fp = sum(1 for exp, pred in zip(expected_list, predicted_list) if exp != label and pred == label)
        fn = sum(1 for exp, pred in zip(expected_list, predicted_list) if exp == label and pred != label)

        total_actual = tp + fn
        total_predicted = tp + fp

        precision = round(tp / total_predicted, 4) if total_predicted > 0 else 0.0
        recall = round(tp / total_actual, 4) if total_actual > 0 else 0.0
        f1 = round((2 * precision * recall) / (precision + recall), 4) if (precision + recall) > 0 else 0.0

        metrics[label] = PerToolMetrics(
            tool=label,
            true_positives=tp,
            false_positives=fp,
            false_negatives=fn,
            precision=precision,
            recall=recall,
            f1_score=f1,
            total_actual=total_actual,
            total_predicted=total_predicted,
        )

    return metrics
