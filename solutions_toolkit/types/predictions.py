from typing import List, Dict
from collections import defaultdict
import pandas as pd


class Predictions():
    def __init__(self, predictions: List[dict]):
        self.preds = predictions

    @property
    def by_label(self) -> Dict[list]:
        prediction_label_map = defaultdict(list)
        for pred in self.preds:
            prediction_label_map[pred["label"]].append(pred)
        return prediction_label_map
        
    def remove_by_confidence(self, confidence=0.95):
        pass

    def _select_max_confidence(self, label):
        max_pred = {"confidence": 0}
        for pred in self.by_label[label]:
            if pred["confidence"] > max_pred["confidence"]:
                max_pred = pred
        return max_pred

    def select
    
    def to_csv(self, save_path: str):
        pass

    



    






