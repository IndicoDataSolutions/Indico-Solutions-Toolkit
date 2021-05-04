from typing import List, Dict
from collections import defaultdict
import pandas as pd


class Predictions:
    def __init__(self, predictions: List[dict]):
        self.preds = predictions

    @property
    def by_label(self) -> Dict[str, list]:
        prediction_label_map = defaultdict(list)
        for pred in self.preds:
            prediction_label_map[pred["label"]].append(pred)
        return prediction_label_map

    def remove_by_confidence(self, confidence=0.95, labels=None):
        for pred in self.preds:
            label = pred["label"]
            if labels and label not in labels:
                continue
            if pred["confidence"][label] < confidence:
                self.preds.remove(pred)

    def select_max_confidence(self, labels: list):
        for label in labels:
            max_pred = self._select_max_confidence(label)
            self._remove_predictions_by_label(label)
            self.preds.append(max_pred)

    def _select_max_confidence(self, label):
        max_pred = None
        for pred in self.by_label[label]:
            if (
                not max_pred
                or pred["confidence"][label] > max_pred["confidence"][label]
            ):
                max_pred = pred
        return max_pred

    def _remove_predictions_by_label(self, label):
        for pred in self.preds:
            if pred["label"] == label:
                self.preds.remove(pred)

    def to_csv(self, save_path: str):
        df = pd.DataFrame(self.preds)
        df.to_csv(save_path, index=False)

    def by_label_to_csv(self, save_path: str):
        df = pd.DataFrame(list(self.by_label.items()), columns=["label_names", "labels_list"])
        df.to_csv(save_path, index=False)
