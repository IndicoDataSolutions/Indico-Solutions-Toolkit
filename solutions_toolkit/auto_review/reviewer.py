from collections import defaultdict

from solutions_toolkit.auto_review.field_config import ReviewConfiguration
from solutions_toolkit.auto_review.auto_review_functions import (
    accept_by_confidence,
    reject_by_confidence,
    reject_by_min_character_length,
    reject_by_max_character_length,
    accept_by_all_match_and_confidence,
    split_merged_values,
    remove_by_confidence,
)

# TODO: make it so people can add functions to REVIEWERS
REVIEWERS = {
    "accept_by_confidence": accept_by_confidence,
    "reject_by_confidence": reject_by_confidence,
    "reject_by_min_character_length": reject_by_min_character_length,
    "reject_by_max_character_length": reject_by_max_character_length,
    "accept_by_all_match_and_confidence": accept_by_all_match_and_confidence,
    "split_merged_values": split_merged_values,
    "remove_by_confidence": remove_by_confidence,
}


class Reviewer:
    """
    Class for programatically reviewing workflow predictions

    Example Usage:

    reviewer = Reviewer(
        predictions, model_name, review_config
    )
    reviewer.apply_review()

    # Get your updated predictions
    updated_predictions: Dict[str, List[dict]] = reviewer.updated_predictions
    """

    def __init__(
        self,
        predictions: Dict[str, List[dict]],
        model_name: str,
        review_config: ReviewConfiguration,
    ):
        self.field_config = review_config.field_config
        self.reviewers = self.merge_dict(review_config.custom_functions)
        self.model_name = model_name
        self.predictions = predictions[self.model_name]
        self.updated_predictions = predictions[self.model_name]

    def merge_dict(custom_functions):
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
            kwargs = fn_config["kwargs"] if fn_config["kwargs"] else {}
            self.updated_predictions = review_fn(**kwargs)
