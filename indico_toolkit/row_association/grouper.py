"""Associate row items"""
from indico_toolkit.types import Predictions
from typing import List, Union, Iterable
from collections import defaultdict
from copy import deepcopy
import os
import json


class Association:
    """
    Class for assigning row_number to line item fields given workflow predictions

    Example Usage:

    litems = Association(
            line_item_fields=["line_value", "line_date"],
            predictions=[{"label": "line_date", "start": 12, "text": "1/2/2021".....}]
        )
    litems.get_bounding_boxes(ocr_tokens=[{"postion"...,},])
    litems.assign_row_number()

    # Get your updated predictions
    updated_preds: List[dict] = litems.updated_predictions
    """

    def __init__(
        self,
        predictions: Union[List[dict], Predictions],
        line_item_fields: Iterable[str] = None,
    ):
        """
        Args:
        predictions (List[dict]): List of extraction predictions
        line_item_fields (Iterable[str]): Fields/labels to include as line item values, other values
                                      will not be assigned a row_number. If None, treats all fields 
                                      as line item fields.

        """
        if isinstance(predictions, Predictions):
            predictions = predictions.to_list()
        if line_item_fields is None:
            print("No line item fields provided. Will treat all predictions as line items")
            line_item_fields = Predictions.get_extraction_labels_set(predictions)
        self.line_item_fields: Iterable[str] = line_item_fields
        self.predictions: List[dict] = predictions
        self._line_item_predictions: List[dict] = []
        self._non_line_item_predictions: List[dict] = []
        self._errored_predictions: List[dict] = []

    @property
    def updated_predictions(self) -> Predictions:
        return Predictions(
            self._line_item_predictions
            + self._non_line_item_predictions
            + self._errored_predictions
        )

    @staticmethod
    def match_pred_to_token(
        pred: dict, ocr_tokens: List[dict], raise_for_no_match: bool = True
    ):
        """
        Match and add bounding box metadata to prediction.

        Args:
            pred (dict): Indico extraction model prediction
            ocr_tokens (List[dict]): List of OCR tokens

        Raises:
            ValueError: No matching token was found

        Returns:
            [int]: index in ocr tokens where prediction matched
        """
        no_match = True
        match_token_index = 0
        for ind, token in enumerate(ocr_tokens):
            if no_match and sequences_overlap(token["doc_offset"], pred):
                _add_bounding_metadata_to_pred(pred, token)
                no_match = False
                match_token_index = ind
            elif sequences_overlap(token["doc_offset"], pred):
                _update_bounding_metadata_for_pred(pred, token)
            elif token["doc_offset"]["start"] > pred["end"]:
                break
        _check_if_token_match_found(pred)
        return match_token_index

    def get_bounding_boxes(
        self, ocr_tokens: List[dict], raise_for_no_match: bool = True,
    ):
        """
        Adds keys for bounding box top/bottom/left/right and page number to line item predictions
        Args:
        ocr_tokens (list of dicts): OCR tokens from 'ondocument' config (workflow default)
        raise_for_no_match (bool): raise exception if a matching token isn't found for a prediction
        """
        if len(self.predictions) == 0:
            raise Exception(
                "Make sure you instantiated the class with a list of predictions"
            )
        predictions = deepcopy(self.predictions)
        predictions = self._remove_unneeded_predictions(predictions)
        predictions = self.sort_predictions_by_start_index(predictions)
        match_index = 0
        for pred in predictions:
            try:
                match_index = self.match_pred_to_token(
                    pred, ocr_tokens[match_index:], raise_for_no_match
                )
                self._line_item_predictions.append(pred)
                continue
            except ValueError as e:
                if raise_for_no_match:
                    raise ValueError(e)
                else:
                    print(f"Ignoring Error: {e}")
                    self._errored_predictions.append(pred)

    def assign_row_number(self):
        """
        Adds a row_number:int key/val pair based on bounding box position and page

        Updates:
        self._line_item_predictions (list of dicts): predictions with row_number added
        """
        starting_pred = self._get_first_valid_line_item_pred()
        max_top = starting_pred["bbTop"]
        min_bot = starting_pred["bbBot"]
        page_number = starting_pred["page_num"]
        row_number = 1
        for pred in self._line_item_predictions:
            if pred["bbTop"] > min_bot or pred["page_num"] != page_number:
                row_number += 1
                page_number = pred["page_num"]
                max_top, min_bot = pred["bbTop"], pred["bbBot"]
            else:
                max_top = min(pred["bbTop"], max_top)
                min_bot = max(pred["bbBot"], min_bot)
            pred["row_number"] = row_number

    def get_line_items_in_groups(self) -> List[List[dict]]:
        """
        After row number has been assigned to predictions, returns line item predictions as a
        list of lists where each list is a row.
        """
        rows = defaultdict(list)
        for pred in self._line_item_predictions:
            rows[pred["row_number"]].append(pred)
        return list(rows.values())

    @staticmethod
    def sort_predictions_by_start_index(predictions: List[dict]) -> List[dict]:
        return sorted(predictions, key=lambda x: x["start"])

    def _remove_unneeded_predictions(self, predictions: List[dict]) -> List[dict]:
        """
        Remove predictions that are not line item fields or don't have valid start/end index data
        """
        valid_line_item_preds = []
        for pred in predictions:
            if not self.is_line_item_pred(pred):
                self._non_line_item_predictions.append(pred)
            elif Predictions.is_manually_added_prediction(pred):
                pred["error"] = "Can't match tokens for manually added prediction"
                self._errored_predictions.append(pred)
            else:
                valid_line_item_preds.append(pred)
        return valid_line_item_preds

    def is_line_item_pred(self, pred: dict):
        if pred["label"] in self.line_item_fields:
            return True
        return False

    def _get_first_valid_line_item_pred(self) -> dict:
        if len(self._line_item_predictions) == 0:
            raise Exception(
                "Whoops! You have no line_item_fields predictions. Did you run get_bounding_boxes?"
            )
        return self._line_item_predictions[0]


def sequences_overlap(x: dict, y: dict) -> bool:
    """
    Boolean return value indicates whether or not seqs overlap
    """
    return x["start"] < y["end"] and y["start"] < x["end"]


def _add_bounding_metadata_to_pred(pred: dict, token: dict):
    pred["bbTop"] = token["position"]["bbTop"]
    pred["bbBot"] = token["position"]["bbBot"]
    pred["bbLeft"] = token["position"]["bbLeft"]
    pred["bbRight"] = token["position"]["bbRight"]
    pred["page_num"] = token["page_num"]


def _check_if_token_match_found(pred: dict):
    if "bbTop" not in pred:
        pred["error"] = "No matching token found for line item field"
        raise ValueError(f"Couldn't match a token to this prediction:\n{pred}")


def _update_bounding_metadata_for_pred(pred: dict, token: dict):
    pred["bbTop"] = min(token["position"]["bbTop"], pred["bbTop"])
    pred["bbBot"] = max(token["position"]["bbBot"], pred["bbBot"])
    pred["bbLeft"] = min(token["position"]["bbLeft"], pred["bbLeft"])
    pred["bbRight"] = max(token["position"]["bbRight"], pred["bbRight"])
