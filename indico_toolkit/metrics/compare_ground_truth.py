from typing import List
import pprint as p


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

    # TODO import this function from toolkit since it already exists
    def _sequences_overlap(self, x: dict, y: dict) -> bool:
        """
        Boolean return value indicates whether or not seqs overlap
        """
        return x["start"] < y["end"] and y["start"] < x["end"]

    def _get_precision(self, true_p: int, false_p: int) -> float:
        if not true_p:
            precision = 0
        else:
            precision = true_p / (true_p + false_p)
        return precision

    def _get_recall(self, true_p: int, false_n: int) -> float:
        if not true_p:
            recall = 0
        else:
            recall = true_p / (true_p + false_n)
        return recall

    def _get_base_metrics(self, label: str) -> dict:
        true_pos = 0
        false_neg = 0
        false_pos = 0
        recall = 0
        precision = 0

        if not self.predictions.get(label, False):
            false_neg = len(self.ground_truth[label])
        if not self.ground_truth.get(label, False):
            false_pos = len(self.predictions[label])

        if self.predictions.get(label, False) and self.ground_truth.get(label, False):
            for model_pred in self.predictions[label]:
                model_flag = False
                for gt_pred in self.ground_truth[label]:
                    if self._sequences_overlap(
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
                    if self._sequences_overlap(
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

    def _build_metrics_dicts(self) -> dict:
        true_pos = 0
        false_neg = 0
        false_pos = 0
        recall = 0
        precision = 0
        labels = self.labels

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

        all_label_metrics = {label: self._get_base_metrics(label) for label in labels}

        for metric in metrics_types:
            total_amt = 0
            for label in all_label_metrics:
                total_amt += all_label_metrics[label][metric]
                overall_metrics[metric] = total_amt

        overall_metrics["precision"] = self._get_precision(
            overall_metrics["true_positives"], overall_metrics["false_positives"]
        )
        overall_metrics["recall"] = self._get_recall(
            overall_metrics["true_positives"], overall_metrics["false_negatives"]
        )

        self.all_label_metrics = all_label_metrics
        self.overall_metrics = overall_metrics
        return all_label_metrics


# def generate_pred(
#     label="Vendor",
#     conf_level=0.85,
#     start_index=0,
#     end_index=2,
#     text="Chili's",
#     page_num=None,
#     bbTop=0,
#     dHeight=9,
#     bbLeft=0,
#     dRight=29,
# ):
#     return {
#         "label": label,
#         "text": text,
#         "start": start_index,
#         "end": end_index,
#         "confidence": {label: conf_level},
#         #         "page number": page_num,
#         #         "position": {
#         #             "bbTop": bbTop,
#         #             "bbBot": bbTop + dHeight,
#         #             "bbLeft": bbLeft,
#         #             "bbRight": bbLeft + dRight,
#         #         },
#     }


# ground_truth = {
#     "Vendor Name": [
#         generate_pred(start_index=0, end_index=11, label="Vendor Name", text="1"),
#         generate_pred(start_index=22, end_index=31, label="Vendor Name", text="2"),
#         generate_pred(start_index=100, end_index=110, label="Vendor Name", text="3"),
#     ],
#     "Amount": [
#         generate_pred(start_index=10, end_index=21, label="Amount", text="1"),
#         generate_pred(start_index=32, end_index=41, label="Amount", text="2"),
#         generate_pred(start_index=110, end_index=120, label="Amount", text="3"),
#     ],
#     "Date": [
#         generate_pred(start_index=10, end_index=15, label="Date", text="1"),
#         generate_pred(start_index=16, end_index=20, label="Date", text="2"),
#         generate_pred(start_index=110, end_index=120, label="Date", text="3"),
#     ],
#     "Address": [
#         generate_pred(start_index=10, end_index=35, label="Address", text="1"),
#         generate_pred(start_index=500, end_index=520, label="Address", text="2"),
#         generate_pred(start_index=600, end_index=620, label="Address", text="3"),
#     ],
#     "Business Category": [
#         generate_pred(
#             start_index=10, end_index=35, label="Business Category", text="1"
#         ),
#         generate_pred(
#             start_index=50, end_index=60, label="Business Category", text="2"
#         ),
#         generate_pred(
#             start_index=71, end_index=79, label="Business Category", text="3"
#         ),
#     ],
#     "City": [
#         generate_pred(start_index=10, end_index=35, label="City", text="1"),
#         generate_pred(start_index=50, end_index=60, label="City", text="2"),
#         generate_pred(start_index=71, end_index=79, label="City", text="3"),
#     ],
#     "State": [
#         generate_pred(start_index=10, end_index=35, label="State", text="1"),
#         generate_pred(start_index=500, end_index=520, label="State", text="2"),
#         generate_pred(start_index=600, end_index=620, label="State", text="3"),
#     ],
#     "Zip": [
#         generate_pred(start_index=100, end_index=106, label="Zip", text="1"),
#         generate_pred(start_index=200, end_index=206, label="Zip", text="2"),
#         generate_pred(start_index=300, end_index=306, label="Zip", text="3"),
#         generate_pred(start_index=400, end_index=406, label="Zip", text="4"),
#         generate_pred(start_index=500, end_index=506, label="Zip", text="5"),
#         generate_pred(start_index=600, end_index=606, label="Zip", text="6"),
#     ],
# }
# predictions = {
#     "Vendor Name": [
#         generate_pred(start_index=3, end_index=7, label="Vendor Name", text="A"),
#         generate_pred(start_index=32, end_index=41, label="Vendor Name", text="B"),
#     ],
#     "Amount": [
#         generate_pred(start_index=13, end_index=17, label="Amount", text="A"),
#         generate_pred(start_index=18, end_index=22, label="Amount", text="B"),
#         generate_pred(start_index=42, end_index=51, label="Amount", text="C"),
#     ],
#     "Date": [
#         generate_pred(start_index=13, end_index=17, label="Date", text="A"),
#         generate_pred(start_index=18, end_index=22, label="Date", text="B"),
#         generate_pred(start_index=42, end_index=51, label="Date", text="C"),
#     ],
#     "Address": [
#         generate_pred(start_index=10, end_index=35, label="Address", text="A"),
#         generate_pred(start_index=500, end_index=522, label="Address", text="B"),
#         generate_pred(start_index=600, end_index=618, label="Address", text="C"),
#         generate_pred(start_index=700, end_index=710, label="Address", text="D"),
#     ],
#     "Business Category": [
#         generate_pred(
#             start_index=36, end_index=40, label="Business Category", text="A"
#         ),
#         generate_pred(
#             start_index=61, end_index=70, label="Business Category", text="B"
#         ),
#         generate_pred(
#             start_index=80, end_index=90, label="Business Category", text="C"
#         ),
#         generate_pred(
#             start_index=700, end_index=710, label="Business Category", text="D"
#         ),
#     ],
#     "PO Number": [
#         generate_pred(start_index=36, end_index=40, label="PO Number", text="A"),
#         generate_pred(start_index=61, end_index=70, label="PO Number", text="B"),
#         generate_pred(start_index=80, end_index=90, label="PO Number", text="C"),
#         generate_pred(start_index=700, end_index=710, label="PO Number", text="D"),
#     ],
#     "State": [
#         generate_pred(start_index=10, end_index=35, label="State", text="A"),
#         generate_pred(start_index=500, end_index=522, label="State", text="B"),
#     ],
#     "Zip": [
#         generate_pred(start_index=100, end_index=106, label="Zip", text="A"),
#         generate_pred(start_index=200, end_index=206, label="Zip", text="B"),
#         generate_pred(start_index=300, end_index=306, label="Zip", text="C"),
#         generate_pred(start_index=400, end_index=406, label="Zip", text="D"),
#         generate_pred(start_index=500, end_index=506, label="Zip", text="E"),
#         generate_pred(start_index=600, end_index=606, label="Zip", text="F"),
#         generate_pred(start_index=700, end_index=706, label="Zip", text="G"),
#         generate_pred(start_index=800, end_index=806, label="Zip", text="H"),
#     ],
# }
