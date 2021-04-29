from typing import List
from collections import defaultdict
import pandas as pd


class Predictions():
    def __init__(self, predictions: List[dict]):
        self.predictions = predictions
        
    def remove_by_confidence(self, confidence=0.95):
        pass

    def _select_max_confidence(self, label):
        # Take highest confidence within each class in label
        pass
    
    @property
    # preds["label"]
    # maybe def __dict__()
    def by_label(self):
        prediction_label_map = defaultdict(list)
        for pred in self.predictions:
            label = pred["label"]
            prediction_label_map[label].append(pred)
        return prediction_label_map
    
    def to_csv(self, save_path: str):
        pass

    



    






