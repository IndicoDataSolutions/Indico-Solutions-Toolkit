from typing import Dict
import pandas as pd

from indico_toolkit.pipelines import FileProcessing


class Classifications:
    """
    Functionality for classification predictions
    """
    def __init__(self, predictions: dict):
        self._preds = predictions

    @property
    def label(self) -> str:
        return self._preds["label"]

    @property
    def labels(self) -> list:
        return list(self.confidence_scores.keys())

    def set_confidence_key_to_max_value(self):
        """
        Overwite confidence dictionary to just max confidence float
        """
        self._preds["confidence"] = self._preds["confidence"][self.label]
    
    @property
    def confidence_scores(self) -> Dict[str, float]:
        return self._preds["confidence"]

    def to_csv(self, save_path, filename: str = "", append_if_exists: bool = True) -> None:
        results = {filename: self._preds}
        df = pd.DataFrame(results).transpose()
        df["filename"] = filename
        if append_if_exists and FileProcessing.file_exists(save_path):
            df.to_csv(save_path, mode="a", header=False, index=False)
        else:
            df.to_csv(save_path, index=False)
