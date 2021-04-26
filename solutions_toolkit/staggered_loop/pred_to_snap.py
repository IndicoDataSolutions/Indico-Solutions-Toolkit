from typing import List
from solutions_toolkit.indico_wrapper import DocExtraction

KEYS_TO_REMOVE_FROM_PREDICTION = ["confidence", "text"]

# TODO: incorporate Workflow class -> i.e. get reviewed predictions for workflow/ submission IDs, OCR text,
# and (optional) filename
# TODO: add method to write to snapshot-like CSV


class StaggeredLoop:
    def __init__(self, workflow_id: int, submission_ids: List[int] = []):
        self._keys_to_remove_from_prediction = KEYS_TO_REMOVE_FROM_PREDICTION

    def convert_predictions_for_snapshot(self, predictions: List[dict]):
        reformatted_predictions = []
        for pred in predictions:
            if self.is_not_manually_added_prediction(pred):
                self._remove_unneeded_keys(pred)
                reformatted_predictions.append(pred)
        return reformatted_predictions

    def is_not_manually_added_prediction(self, prediction: dict):
        if isinstance(prediction["start"], int) and isinstance(prediction["end"], int):
            if prediction["end"] > prediction["start"]:
                return True
        return False

    def _remove_unneeded_keys(self, prediction: dict):
        for key_to_remove in self._keys_to_remove_from_prediction:
            prediction.pop(key_to_remove, None)
