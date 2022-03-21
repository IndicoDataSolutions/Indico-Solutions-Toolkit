from __future__ import (
    annotations,
)  # from 3.10, don't need for same class reference in class method
from typing import List, Union, Tuple
import pandas as pd
import os
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
        """
        Combine and manipulate a Teach Task's snapshot.

        Args:
            path_to_snapshot (str): path to Snapshot CSV
            text_col (str, optional): Column with text, will be inferred if not provided. Defaults to None.
            label_col (str, optional): Column with labels, will be inferred if not provided. Defaults to None.
            file_name_col (str, optional): Column with file names, will be inferred if not provided. Defaults to None.
        """
        self.path_to_snapshot = path_to_snapshot
        self.df: pd.DataFrame = pd.read_csv(path_to_snapshot)
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
        """
        Remove unwanted labels from label column
        Args:
            labels_to_remove (List[str]): the labels you'd like to remove
        """
        updated_predictions = []
        for label_set in self.df[self.label_col]:
            updated_predictions.append(
                [i for i in label_set if i["label"] not in labels_to_remove]
            )
        self.df[self.label_col] = updated_predictions

    def standardize_column_names(
        self,
        text_col: str = "source",
        label_col: str = "target",
        file_name_col: str = "file_name",
    ):
        """
        To allow merging/appending snapshots, standardize the key column headers
        """
        self.df.rename(
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
            self.df.drop(labels=columns_to_drop, axis=1, inplace=True)
        else:
            self.df = self.df[[self.label_col, self.text_col, self.file_name_col]]

    def append(self, snap_to_add: Snapshot):
        """
        Append the rows from another Snapshot to this snapshot. Ensure column names are standardized beforehand.
        Args:
            snap_to_add (Snapshot): Snapshot to add
        """
        self._assert_key_column_names_match(snap_to_add)
        self.df = pd.concat([self.df, snap_to_add.df], ignore_index=True)

    def get_extraction_label_names(self):
        """
        Return a list of all labeled classes in an extraction snapshot.
        """
        label_column = self.df[self.label_col].tolist()
        label_set = set()
        for labels in label_column:
            for label in labels:
                label_set.add(label["label"])
        return sorted(list(label_set))

    def merge_by_file_name(
        self,
        snap_to_merge: Snapshot,
        ensure_identical_text: bool = True,
    ):
        """
        Merge extraction labels for identical files. Merge is 'left' and file names / rows only present
        in 'snap_to_merge' are excluded.
        Args:
            snap_to_merge (Snapshot): Snapshot you want to merge
            ensure_identical_text (bool, optional): Require document text to be identical for common file name.
                                                    Defaults to True.
        """
        self._assert_key_column_names_match(snap_to_merge)
        suffix = "_to_merge"
        merged = pd.merge(
            self.df,
            snap_to_merge.df,
            how="left",
            on=self.file_name_col,
            suffixes=(None, suffix),
        )
        updated_labels = []
        unmatched_files = []
        for _, row in merged.iterrows():
            to_merge_label = f"{self.label_col}{suffix}"
            labels = row[self.label_col]
            if isinstance(row[to_merge_label], list):
                if ensure_identical_text:
                    try:
                        assert row[self.text_col] == row[f"{self.text_col}{suffix}"]
                    except AssertionError:
                        raise ToolkitInputError(
                            f"Text from {row[self.file_name_col]} doesn't match"
                        )
                labels.extend(row[to_merge_label])
            else:
                unmatched_files.append(row[self.file_name_col])
            updated_labels.append(labels)
        if unmatched_files:
            print(f"No new labels were added for these files: {unmatched_files}")
        merged[self.label_col] = updated_labels
        self.df = merged.drop([i for i in merged.columns if i.endswith(suffix)], axis=1)

    def to_csv(
        self,
        path: str,
        only_keep_key_columns: bool = True,
        convert_label_col_to_json: bool = True,
    ):

        if only_keep_key_columns:
            self.drop_unneeded_columns()
        if convert_label_col_to_json:
            self._convert_col_to_json(self.label_col)
        self.df.to_csv(path, index=False)

    def get_all_labeled_text(
        self, label_name: str, return_per_document: bool = False
    ) -> Union[List[List[str]], List[str]]:
        """
        Get all of the text that was tagged for a given label
        Args:
            label_name (str): name of the label
            return_per_document (bool, optional): return a list per document or one list with everything.
                                                  Defaults to False.
        """
        available_labels = self.get_extraction_label_names()
        if label_name not in available_labels:
            raise ToolkitInputError(
                f"'{label_name}' not present among available labels: {available_labels}"
            )
        all_labeled_text = []
        for text, labels in zip(self.df[self.text_col], self.df[self.label_col]):
            text_found = []
            for lab in labels:
                if lab["label"] == label_name:
                    text_found.append(text[lab["start"] : lab["end"]])
            if return_per_document:
                all_labeled_text.append(text_found)
            else:
                all_labeled_text.extend(text_found)
        return all_labeled_text

    def split_and_write_to_csv(
        self, output_dir: str, num_splits: int = 5, output_base_name: str = "split_num"
    ) -> None:
        """
        For large files that may face memory constraints, split the file into multiple CSVs and write
        to disk.
        Args:
            output_dir (str): Location where split files will be written.
            num_splits (int, optional): The number of splits of the CSV. Defaults to 5.
            output_base_name (str, optional): The base name of the split CSVs: Defaults to "split_num".
                                              So files would be "split_num_1.csv", "split_num_2.csv", etc.
        """
        split_length = self.number_of_samples // num_splits
        rows_taken = 0
        for i in range(1, num_splits + 1):
            if i == num_splits:
                sub_df = self.df.iloc[rows_taken:]
            else:
                sub_df = self.df.iloc[rows_taken : rows_taken + split_length]
            split_file_loc = os.path.join(output_dir, f"{output_base_name}_{i}.csv")
            sub_df.to_csv(split_file_loc, index=False)
            rows_taken += split_length
            print(f"Wrote split {i} of {num_splits}: {split_file_loc}")

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
            self.df[self.label_col] = self.df[self.label_col].apply(json.loads)
        except (TypeError, JSONDecodeError):
            if isinstance(self.df[self.label_col].iloc[0], list):
                return  # json column already converted
            raise ToolkitInputError(
                f"{self.label_col} doesn't contain valid extraction labels"
            )

    def _assert_key_column_names_match(self, snapshot: Snapshot):
        try:
            assert self == snapshot
        except AssertionError:
            raise ToolkitInputError(
                f"Column names don't match for this Snapshot: {snapshot}"
            )

    def _convert_col_to_json(self, column: str):
        self.df[column] = self.df[column].apply(json.dumps)

    def _infer_text_col(self):
        if "text" in self.df.columns:
            self.text_col = "text"
        elif "document" in self.df.columns:
            self.text_col = "document"
        elif "source" in self.df.columns:
            self.text_col = "source"
        else:
            error_message = self._format_column_error_message("text_col")
            raise ToolkitInstantiationError(error_message)

    def _infer_label_col(self):
        question_col = [
            col for col in self.df.columns if "question" in col or "target" in col
        ]
        if len(question_col) != 1:
            error_message = self._format_column_error_message("label_col")
            raise ToolkitInstantiationError(error_message)
        self.label_col = question_col[0]

    def _infer_file_name_col(self):
        file_name_col = [col for col in self.df.columns if "file_name" in col]
        if len(file_name_col) != 1:
            error_message = self._format_column_error_message("file_name_col")
            raise ToolkitInstantiationError(error_message)
        self.file_name_col = file_name_col[0]

    def _format_column_error_message(self, column):
        column_list = list(self.df.columns)
        return f"You must set attribute '{column}' from {column_list}"

    def __repr__(self):
        return f"Snapshot, label_col: {self.label_col}, loc: {self.path_to_snapshot}"

    @property
    def number_of_samples(self) -> int:
        return self.df.shape[0]

    @property
    def shape(self) -> Tuple[int, int]:
        return self.df.shape
