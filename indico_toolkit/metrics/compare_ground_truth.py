from indico_toolkit.association.association import sequences_overlap
from indico_toolkit.types.extractions import Extractions


class CompareGroundTruth:
    """
    Compare a set of ground truths against a set of model predictions on a per document basis.
    span_type
    """

    def __init__(self, ground_truth: list, predictions: list, span_type: str):
        self.span_type = (
            span_type  # Span type string needs to be equal to "exact" or "overlap"
        )
        self.gt_by_label: dict = Extractions(ground_truth).to_dict_by_label
        self.preds_by_label: dict = Extractions(predictions).to_dict_by_label
        self.labels: list[str] = list(
            set(list(self.gt_by_label) + list(self.preds_by_label))
        )
        self.all_label_metrics: dict = None
        self.overall_metrics: dict = None

    def set_all_label_metrics(self) -> None:
        self.all_label_metrics = {
            label: self._get_base_metrics(label, self.span_type)
            for label in self.labels
        }

    def set_overall_metrics(self) -> None:
        self.set_all_label_metrics

        metrics_types = [
            "true_positives",
            "false_positives",
            "false_negatives",
        ]

        self.overall_metrics = {
            "true_positives": 0,
            "false_positives": 0,
            "false_negatives": 0,
        }

        for metric in metrics_types:
            total_amt = 0
            for label in self.all_label_metrics:
                total_amt += self.all_label_metrics[label][metric]
                self.overall_metrics[metric] = total_amt

        self.overall_metrics["precision"] = self._get_precision(
            self.overall_metrics["true_positives"],
            self.overall_metrics["false_positives"],
        )
        self.overall_metrics["recall"] = self._get_recall(
            self.overall_metrics["true_positives"],
            self.overall_metrics["false_negatives"],
        )

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

    def _sequences_exact(self, x: dict, y: dict) -> bool:
        """
        Boolean return value indicates whether or not seqs are exact
        """
        return x["start"] == y["start"] and x["end"] == y["end"]

    # TODO add in other span type functions, ultimately move them to toolkit, within association

    def _get_base_metrics(self, label: str, span_type: str) -> dict:
        """
        With the current overlap span type calculation, if 2 separate predictions each overlap with a single ground truth, each pred is counted as a true positive. (That is why we don't break out of the loop once a true positive is found.)
        """
        true_pos = 0
        false_neg = 0
        false_pos = 0
        span_types = {"overlap": sequences_overlap, "exact": self._sequences_exact}
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
