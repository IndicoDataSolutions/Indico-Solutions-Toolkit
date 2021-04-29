from typing import List
from collections import defaultdict
import pandas as pd


class Predictions():
    def __init__(self, predictions: List[dict]):
        self.predictions = predictions
        self.updated_predictions = predictions
        
    def remove_by_confidence(self, confidence=0.95):
        pass

    def choose_top_confidence(self):
        pass
    
    @property
    def by_label(self):
        prediction_label_map = defaultdict(list)
        for pred in self.predictions:
            label = pred["label"]
            prediction_label_map[label].append(pred)
        return prediction_label_map
    
    def save_to_csv(self, save_path: str, predictions: List[dict] = None):
        if not predictions:
            predictions = self.updated_predictions
        pass

    






