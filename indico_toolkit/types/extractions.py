from typing import List, Dict, Set
from collections import defaultdict, Counter
import pandas as pd
from copy import deepcopy
from indico_toolkit.pipelines import FileProcessing

# TODO: add property to list all predicted labels


class Extractions:
    """
    Functionality for common extraction prediction use cases
    """

    def __init__(self, predictions: List[dict]):
        self._preds = predictions

    @property
    def to_dict_by_label(self) -> Dict[str, list]:
        prediction_label_map = defaultdict(list)
        for pred in self._preds:
            prediction_label_map[pred["label"]].append(pred)
        return prediction_label_map

    @property
    def num_predictions(self) -> int:
        return len(self._preds)

    def remove_by_confidence(self, confidence: float = 0.95, labels: List[str] = None):
        """
        Remove predictions that are less than given confidence
        Args:
            confidence (float, optional): confidence theshold. Defaults to 0.95.
            labels (List[str], optional): Labels where this applies, if None applies to all. Defaults to None.
        """
        high_conf_preds = []
        for pred in self._preds:
            label = pred["label"]
            if labels and label not in labels:
                high_conf_preds.append(pred)
            elif pred["confidence"][label] >= confidence:
                high_conf_preds.append(pred)
        self._preds = high_conf_preds

    def remove_except_max_confidence(self, labels: List[str]):
        """
        Removes all predictions except the highest confidence within each specified class
        """
        label_set = self.label_set
        for label in labels:
            if label not in label_set:
                continue
            max_pred = self._select_max_confidence(label)
            self._remove_all_by_label(label)
            self._preds.append(max_pred)

    def set_confidence_key_to_max_value(self, inplace: bool = True):
        """
        Overwite confidence dictionary to just max confidence float
        """
        if inplace:
            self._set_confidence_key_to_max_value(self._preds)
        else:
            return self._set_confidence_key_to_max_value(deepcopy(self._preds))

    @staticmethod
    def _set_confidence_key_to_max_value(preds):
        for pred in preds:
            pred["confidence"] = pred["confidence"][pred["label"]]
        return preds

    def remove_keys(
        self, keys_to_remove: List[str] = ["start", "end"], inplace: bool = True
    ):
        if inplace:
            self._remove_keys(self._preds, keys_to_remove)
        else:
            return self._remove_keys(deepcopy(self._preds), keys_to_remove)

    @staticmethod
    def _remove_keys(preds, keys_to_remove: List[str] = ["start", "end"]):
        for pred in preds:
            for key in keys_to_remove:
                pred.pop(key)
        return preds

    def remove_human_added_predictions(self):
        """
        Remove predictions that were not added by the model (i.e. added by scripted or human review)
        """
        self._preds = [
            i for i in self._preds if not self.is_manually_added_prediction(i)
        ]

    def to_list(self):
        return self._preds

    @staticmethod
    def is_manually_added_prediction(prediction: dict) -> bool:
        if isinstance(prediction["start"], int) and isinstance(prediction["end"], int):
            if prediction["end"] > prediction["start"]:
                return False
        return True

    @staticmethod
    def get_extraction_labels_set(predictions: List[dict]) -> Set[str]:
        return set([i["label"] for i in predictions])

    @property
    def label_set(self):
        return set([i["label"] for i in self._preds])

    def _select_max_confidence(self, label):
        max_pred = None
        confidence = 0
        for pred in self[label]:
            pred_confidence = pred["confidence"][label]
            if pred_confidence >= confidence:
                max_pred = pred
                confidence = pred_confidence
        return max_pred

    @property
    def label_count_dict(self) -> Dict[str, int]:
        """
        Get count of occurrences of each label
        """
        return dict(Counter(i["label"] for i in self._preds))

    def _remove_all_by_label(self, label):
        new_preds = []
        for pred in self._preds:
            if pred["label"] != label:
                new_preds.append(pred)
        self._preds = new_preds

    def __len__(self):
        return len(self._preds)

    def __repr__(self):
        return f"Prediction Class, {self.num_predictions} Predictions:\n\n{self._preds}"

    def __getitem__(self, label: str) -> List[dict]:
        return [i for i in self._preds if i["label"] == label]

    def to_csv(
        self, save_path: str, filename: str = "", append_if_exists: bool = True
    ) -> None:
        """
        Write three column CSV ('confidence', 'label', 'text')
        Args:
            save_path (str): path to write CSV
            filename (str, optional): the file where the preds were derived from. Defaults to "".
        """
        preds = self.set_confidence_key_to_max_value(inplace=False)
        preds = self._remove_keys(preds, keys_to_remove=["start", "end"])
        df = pd.DataFrame(preds)
        df["filename"] = filename
        if append_if_exists and FileProcessing.file_exists(save_path):
            df.to_csv(save_path, mode="a", header=False, index=False)
        else:
            df.to_csv(save_path, index=False)
