from typing import List
from .predictions import Predictions
from indico_toolkit import ToolkitStatusError, ToolkitInputError


class WorkflowResult:
    def __init__(self, result: dict, model_name: str = None):
        """
        Common functionality for workflow result object
        Args:
            result (dict): raw workflow result object
            model_name (str, optional): Extraction/Classification model name . Defaults to None.
        """
        self.result = result
        self.model_name = model_name

    def _check_is_valid_model_name(self) -> None:
        if self.model_name not in self.available_model_names:
            raise ToolkitInputError(
                f"{self.model_name} is not an available model name. Options: {self.available_model_names}"
            )

    def __repr__(self):
        return f"WorkflowResult object, Submission ID: {self.submission_id}"

    @property
    def predictions(self) -> Predictions:
        """
        Return predictions without human review
        """
        self._set_model_name()
        preds = self.document_results[self.model_name]
        if "pre_review" in preds:
            preds = preds["pre_review"]
        return Predictions.get_obj(preds)

    @property
    def post_review_predictions(self) -> List[dict]:
        self._set_model_name()
        try:
            return Predictions.get_obj(self.document_results[self.model_name]["final"])
        except (KeyError, TypeError):
            raise ToolkitStatusError(
                f"Submission {self.submission_id} has no 'final' predictions. Has it completed human review?"
            )

    def _set_model_name(self):
        """
        Attempts to select the relevant model name if not already specified.
        Raises error if multiple models are available and self.model_name specified.
        """
        if self.model_name:
            self._check_is_valid_model_name()
        elif len(self.available_model_names) > 1:
            raise ToolkitInputError(
                f"Multiple models available, you must set self.model_name to one of {self.available_model_names}"
            )
        else:
            self.model_name = self.available_model_names[0]

    @property
    def etl_url(self) -> str:
        return self.result["etl_output"]

    @property
    def document_results(self) -> dict:
        return self.result["results"]["document"]["results"]

    @property
    def available_model_names(self) -> List[str]:
        return list(self.document_results.keys())

    @property
    def submission_id(self) -> str:
        return self.result["submission_id"]

    @property
    def errors(self) -> list:
        return self.result["errors"]

    @property
    def review_id(self) -> int:
        return self.result["review_id"]

    @property
    def reviewer_id(self) -> int:
        return self.result["reviewer_id"]

    @property
    def review_notes(self) -> int:
        return self.result["review_notes"]

    @property
    def review_rejected(self) -> int:
        return self.result["review_rejected"]

    @property
    def admin_review(self) -> bool:
        return self.result["admin_review"]
