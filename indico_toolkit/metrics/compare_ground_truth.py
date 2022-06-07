from typing import List
from indico_toolkit.association.association import sequences_overlap, sequences_exact
from indico_toolkit.types.extractions import Extractions
from indico_toolkit.errors import ToolkitInputError


class CompareGroundTruth:
    """
    Compare a set of ground truths against a set of model predictions on a per document basis.
    """

    def __init__(self, ground_truth: List[dict], predictions: List[dict]):
        self.gt_by_label: dict = Extractions(ground_truth).to_dict_by_label
        self.preds_by_label: dict = Extractions(predictions).to_dict_by_label
        self.labels: List[str] = list(
            set(list(self.gt_by_label) + list(self.preds_by_label))
        )
        self.all_label_metrics: dict = None
        self.overall_metrics: dict = None

    def set_all_label_metrics(self, span_type: str = "overlap") -> None:
        """
        The "all_label_metrics" dict includes each label as a key and each label's metrics as the corresponding value.
        """
        if span_type in ["exact", "overlap"]:
            self.all_label_metrics = {
                label: self._get_base_metrics(label, span_type) for label in self.labels
            }
        else:
            raise ToolkitInputError("Invalid span type entered.")

    def set_overall_metrics(self) -> None:
        """
        The "overall_metrics" dict includes the metrics for the entire document. (Key: metric type; value: metric value)
        """
        if self.all_label_metrics is None:
            self.set_all_label_metrics()

        metrics_types = [
            "true_positives",
            "false_positives",
            "false_negatives",
        ]

        overall_metrics = {}

        for metric in metrics_types:
            total_amt = 0
            for label in self.all_label_metrics:
                total_amt += self.all_label_metrics[label][metric]
            overall_metrics[metric] = total_amt

        overall_metrics["precision"] = self._get_precision(
            overall_metrics["true_positives"],
            overall_metrics["false_positives"],
        )
        overall_metrics["recall"] = self._get_recall(
            overall_metrics["true_positives"],
            overall_metrics["false_negatives"],
        )

        self.overall_metrics = overall_metrics

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

    def _get_base_metrics(self, label: str, span_type: str) -> dict:
        """
        With the current overlap span type calculation, if 2 separate predictions
        each overlap with a single ground truth, each pred is counted as a true
        positive. (i.e. There isn't a break out of the loop once a TP is found.)
        """
        # TODO potentially build in choice on the "multiple true positives" per ground truth prediction by adding conditional
        true_pos = 0
        false_neg = 0
        false_pos = 0
        span_types = {"overlap": sequences_overlap, "exact": sequences_exact}
        span_type_func = span_types[span_type]

        if not label in self.preds_by_label:
            false_neg = len(self.gt_by_label[label])
        elif not label in self.gt_by_label:
            false_pos = len(self.preds_by_label[label])
        else:
            for model_pred in self.preds_by_label[label]:
                match_found = False
                for gt_pred in self.gt_by_label[label]:
                    if span_type_func(model_pred, gt_pred):
                        true_pos += 1
                        match_found = True
                if not match_found:
                    false_pos += 1
            for gt_pred in self.gt_by_label[label]:
                match_found = False
                for model_pred in self.preds_by_label[label]:
                    if span_type_func(model_pred, gt_pred):
                        match_found = True
                if not match_found:
                    false_neg += 1

        return {
            "true_positives": true_pos,
            "false_negatives": false_neg,
            "false_positives": false_pos,
            "precision": self._get_precision(true_pos, false_pos),
            "recall": self._get_recall(true_pos, false_neg),
        }
