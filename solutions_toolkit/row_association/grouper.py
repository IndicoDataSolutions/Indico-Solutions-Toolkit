"""Associate row items"""
from typing import List
from collections import defaultdict
from copy import deepcopy
import os
import json

# TODO: fix doc string format


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

    def __init__(self, line_item_fields: List[str], predictions: List[dict] = None):
        """
        Args:
        predictions (List[dict]): List of extraction predictions
        line_item_fields (List[str]): Fields/labels to include as line item values, other values
                                      will not be assigned a row_number
        Attributes populated after running get_bounding_boxes and assign_row_number:
        updated_predictions (List[dict]): predictions updated with row_number
        """
        self.line_item_fields: List[str] = line_item_fields
        self.predictions: List[dict] = predictions
        self._line_item_predictions: List[dict] = []
        self._non_line_item_predictions: List[dict] = []

    @property
    def updated_predictions(self):
        return self._line_item_predictions + self._non_line_item_predictions

    @staticmethod
    def match_pred_to_token(
        pred: dict, ocr_tokens: List[dict], raise_for_no_match: bool = True
    ):
        """
        Match and add bounding box metadata to prediction.

        Args:
            pred (dict): Indico extraction model prediction 
            ocr_tokens (List[dict]): List of OCR tokens
            raise_for_no_match (bool, optional): Raise an exception if no matching token found. Defaults to True.

        Raises:
            Exception: No matching token was found

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
        _check_if_token_match_found(pred, raise_for_no_match)
        return match_token_index

    def get_bounding_boxes(
        self,
        ocr_tokens: List[dict],
        add_boxes_to_all: bool = False,
        raise_for_no_match: bool = True,
        in_place: bool = True,
    ) -> List[dict]:
        """
        Adds keys for bounding box top/bottom and page number to line item extraction predictions, 
        and adds all preds to property self._line_item_predictions
        Args:
        ocr_tokens (list of dicts): OCR tokens from 'ondocument' config (workflow default)
        raise_for_no_match (bool): raise exception if a matching token isn't found for a prediction
        add_boxes_to_all (bool): add bounding box and page number metadata to non line item predictions
        in_place (bool): if False, returns tokens with bounding boxes
        """
        if len(self.predictions) == 0:
            raise Exception(
                "Make sure you instantiated the class with a list of predictions"
            )
        predictions = deepcopy(self.predictions)
        match_index = 0
        for pred in predictions:
            if self.is_line_item_pred(pred):
                match_index = self.match_pred_to_token(
                    pred, ocr_tokens[match_index:], raise_for_no_match
                )
                self._line_item_predictions.append(pred)
            else:
                if add_boxes_to_all:
                    match_index = self.match_pred_to_token(
                        pred, ocr_tokens[match_index:], raise_for_no_match
                    )
                self._non_line_item_predictions.append(pred)
        if not in_place:
            return self.updated_predictions

    def is_line_item_pred(self, pred: dict):
        if pred["label"] in self.line_item_fields:
            return True
        return False

    def assign_row_number(self, in_place: bool = True):
        """
        Adds a row_number:int key/val pair based on bounding box position and page
        Args:
        in_place (bool): if False, returns updated_predictions
        Updates:
        self._line_item_predictions (list of dicts): predictions with row_number added
        """
        starting_pred = self._get_first_valid_line_item_pred()
        max_top = starting_pred["bbTop"]
        min_bot = starting_pred["bbBot"]
        page_number = starting_pred["page_num"]
        row_number = 1
        for pred in self._line_item_predictions:
            if "error" in pred:
                continue
            elif pred["bbTop"] > min_bot or pred["page_num"] != page_number:
                row_number += 1
                page_number = pred["page_num"]
                max_top, min_bot = pred["bbTop"], pred["bbBot"]
            else:
                max_top = min(pred["bbTop"], max_top)
                min_bot = max(pred["bbBot"], min_bot)
            pred["row_number"] = row_number
        if not in_place:
            return self.updated_predictions

    def _get_first_valid_line_item_pred(self) -> dict:
        if len(self._line_item_predictions) == 0:
            raise Exception(
                "Whoops! You have no line_item_fields predictions. Did you run get_bounding_boxes?"
            )
        try:
            return next(
                pred for pred in self._line_item_predictions if "error" not in pred
            )
        except StopIteration:
            raise Exception(
                "No matching tokens were found for your line item predictions"
            )

    def remove_meta_keys_from_dict(
        self, keys_to_remove=("bbTop", "bbBot", "bbLeft", "bbRight")
    ):
        """
        Remove meta keys from prediction dictionaries. Other options that you might want 
        to remove include: "page_num" and/or "row_number", "confidence", etc.
        Args:
            keys_to_remove (tuple, optional): keys to remove from prediction dictionaries. 
        """
        for remove_key in keys_to_remove:
            for pred in self._line_item_predictions:
                pred.pop(remove_key, None)
            for pred in self._non_line_item_predictions:
                pred.pop(remove_key, None)


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


def _check_if_token_match_found(pred: dict, raise_for_no_match: bool = True):
    if "bbTop" in pred:
        return True
    elif not raise_for_no_match:
        _add_metadata_to_unmatched_pred(pred)
    else:
        raise Exception(f"Couldn't match a token to this predicition:\n{pred}")


def _add_metadata_to_unmatched_pred(pred: dict):
    """
    If no token match found and not raising exception, add enough data to be able to process 
    through assign_row_number
    """
    pred["error"] = "No matching token found"
    pred["bbTop"] = None
    pred["bbBot"] = None
    pred["bbLeft"] = None
    pred["bbRight"] = None
    pred["page_num"] = None
    pred["row_number"] = None


def _update_bounding_metadata_for_pred(pred: dict, token: dict):
    pred["bbTop"] = min(token["position"]["bbTop"], pred["bbTop"])
    pred["bbBot"] = max(token["position"]["bbBot"], pred["bbBot"])
    pred["bbLeft"] = min(token["position"]["bbLeft"], pred["bbLeft"])
    pred["bbRight"] = max(token["position"]["bbRight"], pred["bbRight"])
