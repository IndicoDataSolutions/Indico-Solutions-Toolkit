from typing import List
import pandas as pd
import json
from json import JSONDecodeError
from indico_toolkit import ToolkitInstantiationError, ToolkitInputError

# TODO: add functionality for classification snapshots

class Snapshot:
    def __init__(
        self, 
        path_to_snapshot: str, 
        text_col: str = None, 
        label_col: str = None,
        file_name_col: str = None
    ):
        self._df: pd.DataFrame = pd.read_csv(path_to_snapshot)
        self.label_col = label_col
        if label_col is None:
            self._infer_label_col()
        self._convert_col_from_json()
        self.text_col = text_col
        if text_col is None:
            self._infer_text_col()
        self.file_name_col = file_name_col
        if file_name_col is None:
            self._infer_file_name_col()

    def remove_extraction_labels(self, labels_to_remove: List[str]):
        updated_predictions = []
        for label_set in self._df[self.label_col]:
            updated_predictions.append(
                [i for i in label_set if i["label"] not in labels_to_remove]
            )
        self._df[self.label_col] = updated_predictions


    def _convert_col_from_json(self):
        try:
            self._df[self.label_col] = self._df[self.label_col].apply(json.loads)
        except (TypeError, JSONDecodeError):
            if isinstance(self._df[self.label_col].iloc[0], list):
                return # json column already converted
            raise ToolkitInputError(f"{self.label_col} doesn't contain valid extraction labels")


    def _convert_col_to_json(self, column: str):
        self._df[column] = self._df[column].apply(json.dumps)

    def _infer_text_col(self):
        if "text" in self._df.columns:
            self.text_col = "text"
        elif "document" in self._df.columns:
            self.text_col = "document"
        else:
            raise ToolkitInstantiationError(
                f"You must set 'text_col' from {list(self._df.colmns)}"
            )
    
    def _infer_label_col(self):
        question_col = [col for col in self._df.columns if "question" in col]
        if len(question_col) != 1:
            raise ToolkitInstantiationError(
                f"You must set 'label_col' from {list(self._df.colmns)}"
            )
        self.label_col = question_col[0]

    def _infer_file_name_col(self):
        file_name_col = [col for col in self._df.columns if "file_name" in col]
        if len(file_name_col) != 1:
            raise ToolkitInstantiationError(
                f"You must set 'file_name_col' from {list(self._df.colmns)}"
            )
        self.file_name_col = file_name_col[0]
