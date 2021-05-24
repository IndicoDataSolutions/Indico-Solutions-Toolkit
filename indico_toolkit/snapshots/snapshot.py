from __future__ import (
    annotations,
)  # from 3.10, don't need for same class reference in class method
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
        file_name_col: str = None,
    ):
        self.path_to_snapshot = path_to_snapshot
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

    def standardize_column_names(
        self,
        text_col: str = "source",
        label_col: str = "target",
        file_name_col: str = "file_name",
    ):
        self._df.rename(
            mapper={
                self.file_name_col: file_name_col,
                self.text_col: text_col,
                self.label_col: label_col,
            },
            inplace=True,
            errors="raise",
            axis=1,
        )
        self.file_name_col = file_name_col
        self.label_col = label_col
        self.text_col = text_col

    def drop_unneeded_columns(self, columns_to_drop: List[str] = None):
        """
        Keep only text, labels, and file name columns or specify columns to drop by passing them in as a list.
        """
        if columns_to_drop:
            self._df.drop(labels=columns_to_drop, axis=1, inplace=True)
        else:
            self._df = self._df[[self.label_col, self.text_col, self.file_name_col]]

    def append(self, snap_to_add: Snapshot):
        try:
            assert self == snap_to_add
            self._df = self._df.append(snap_to_add._df, ignore_index=True)
        except AssertionError:
            raise ToolkitInputError(f"Column names don't match for this Snapshot: {snap_to_add}")
            
    def __eq__(self, other: Snapshot):
        """
        Check if two snapshots can be merged based on common column names
        """
        return (
            self.label_col == other.label_col
            and self.text_col == other.text_col
            and self.file_name_col == other.file_name_col
        )

    def _convert_col_from_json(self):
        try:
            self._df[self.label_col] = self._df[self.label_col].apply(json.loads)
        except (TypeError, JSONDecodeError):
            if isinstance(self._df[self.label_col].iloc[0], list):
                return  # json column already converted
            raise ToolkitInputError(
                f"{self.label_col} doesn't contain valid extraction labels"
            )

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

    def __repr__(self):
        return f"Snapshot, label_col: {self.label_col}, loc: {self.path_to_snapshot}"
