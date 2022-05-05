from typing import List
from indico_toolkit.association.association import sequences_overlap


class CompareGroundTruth:
    """
    Compare a set of Ground truth against a set of predictions
    """

    def __init__(self, ground_truth, predictions):
        self.ground_truth: List[dict] = ground_truth
        self.predictions: List[dict] = predictions
        self.labels: List[str] = None
        self.all_label_metrics: List[dict] = None
        self.overall_metrics: List[dict] = None

    def _get_labels(self) -> None:
        labels = []

        for label in self.ground_truth:
            if not label in labels:
                labels.append(label)

        for label in self.predictions:
            if not label in labels:
                labels.append(label)

        self.labels = labels

    def _get_precision(self, true_p: int, false_p: int) -> float:
        try:
            precision = true_p / (true_p + false_p)
        except ZeroDivisionError:
            precision = 0
        return precision

    def _get_recall(self, true_p: int, false_n: int) -> float:
        try:
            recall = true_p / (true_p + false_n)
        except ZeroDivisionError:
            recall = 0
        return recall

    def _get_base_metrics(self, label: str) -> dict:
        true_pos = 0
        false_neg = 0
        false_pos = 0
        recall = 0
        precision = 0

        if not label in self.predictions:
            false_neg = len(self.ground_truth[label])
        if not label in self.ground_truth:
            false_pos = len(self.predictions[label])

        if label in self.predictions and label in self.ground_truth:
            for model_pred in self.predictions[label]:
                model_flag = False
                for gt_pred in self.ground_truth[label]:
                    if sequences_overlap(
                        {"start": model_pred["start"], "end": model_pred["end"]},
                        {"start": gt_pred["start"], "end": gt_pred["end"]},
                    ):
                        true_pos += 1
                        model_flag = True
                if not model_flag:
                    false_pos += 1

            for gt_pred in self.ground_truth[label]:
                gt_flag = False
                for model_pred in self.predictions[label]:
                    if sequences_overlap(
                        {"start": model_pred["start"], "end": model_pred["end"]},
                        {"start": gt_pred["start"], "end": gt_pred["end"]},
                    ):
                        gt_flag = True
                if not gt_flag:
                    false_neg += 1

        recall = self._get_recall(true_pos, false_neg)
        precision = self._get_precision(true_pos, false_pos)
        return {
            "true_positives": true_pos,
            "false_negatives": false_neg,
            "false_positives": false_pos,
            "precision": precision,
            "recall": recall,
        }

    def _get_all_label_metrics_dicts(self) -> dict:
        labels = self.labels

        all_label_metrics = {label: self._get_base_metrics(label) for label in labels}
        self.all_label_metrics = all_label_metrics

        return all_label_metrics

    def _get_overall_label_metrics_dict(self) -> dict:
        metrics_types = [
            "true_positives",
            "false_positives",
            "false_negatives",
        ]

        overall_metrics = {
            "true_positives": 0,
            "false_positives": 0,
            "false_negatives": 0,
        }

        for metric in metrics_types:
            total_amt = 0
            for label in self.all_label_metrics:
                total_amt += self.all_label_metrics[label][metric]
                overall_metrics[metric] = total_amt

        overall_metrics["precision"] = self._get_precision(
            overall_metrics["true_positives"], overall_metrics["false_positives"]
        )
        overall_metrics["recall"] = self._get_recall(
            overall_metrics["true_positives"], overall_metrics["false_negatives"]
        )

        self.overall_metrics = overall_metrics
        return overall_metrics
