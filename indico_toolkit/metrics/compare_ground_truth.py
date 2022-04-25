from typing import List
from collections import defaultdict


class CompareGroundTruth:
    """
    Compare a set of Ground truth against a set of predictions
    """

    def __init__(self, ground_truth, predictions):
        self.ground_truth: List[dict] = ground_truth
        self.predictions: List[dict] = predictions
        self.matching_labels: List[str] = None
        self.not_matching_labels: List[str] = None

    def _get_labels(self) -> None:
        ground_truth_labels = []
        predictions_labels = []

        for pred in self.ground_truth:
            if not pred["label"] in ground_truth_labels:
                ground_truth_labels.append(pred["label"])

        for pred in self.predictions:
            if not pred["label"] in predictions_labels:
                predictions_labels.append(pred["label"])

        for label in ground_truth_labels:
            if label in predictions_labels:
                self.matching_labels.append(label)
            else:
                self.not_matching_labels.append(label)
