from collections import defaultdict
from typing import List

from .review_config import ReviewConfiguration
from .auto_review_functions import (
    accept_by_confidence,
    reject_by_confidence,
    reject_by_min_character_length,
    reject_by_max_character_length,
    accept_by_all_match_and_confidence,
    remove_by_confidence,
)


REVIEWERS = {
    "accept_by_confidence": accept_by_confidence,
    "reject_by_confidence": reject_by_confidence,
    "reject_by_min_character_length": reject_by_min_character_length,
    "reject_by_max_character_length": reject_by_max_character_length,
    "accept_by_all_match_and_confidence": accept_by_all_match_and_confidence,
    "remove_by_confidence": remove_by_confidence,
}


class AutoReviewer:
    """
    Class for programatically reviewing workflow predictions

    Example Usage:

    reviewer = AutoReviewer(
        predictions, review_config
    )
    reviewer.apply_review()

    # Get your updated predictions
    updated_predictions: List[dict] = reviewer.updated_predictions
    """

    def __init__(
        self,
        predictions: List[dict],
        review_config: ReviewConfiguration,
    ):
        self.field_config = review_config.field_config
        self.reviewers = self.add_reviewers(review_config.custom_functions)
        self.predictions = predictions
        self.updated_predictions = predictions

    @staticmethod
    def add_reviewers(custom_functions):
        """
        Add custom functions into reviewers
        Overwrites any default reviewers if function names match
        """
        for func_name, func in custom_functions.items():
            REVIEWERS[func_name] = func
        return REVIEWERS

    def apply_reviews(self):
        for fn_config in self.field_config:
            fn_name = fn_config["function"]
            try:
                review_fn = REVIEWERS[fn_name]
            except KeyError:
                raise KeyError(
                    f"{fn_name} function was not found, did you specify it in FieldConfiguration?"
                )
            kwargs = fn_config["kwargs"] if fn_config.get("kwargs") else {}
            self.updated_predictions = review_fn(self.updated_predictions, **kwargs)
