from typing import List
from dataclasses import dataclass
from solutions_toolkit.indico_wrapper import Workflow

KEYS_TO_REMOVE_FROM_PREDICTION = ["confidence", "text"]

# TODO: incorporate Workflow class -> i.e. get reviewed predictions for workflow/ submission IDs, OCR text, 
# and (optional) filename 
# TODO: add method to write to snapshot-like CSV

class StaggeredLoop:
    
    _keys_to_remove_from_prediction = KEYS_TO_REMOVE_FROM_PREDICTION

    def __init__(self, workflow_id: int, submission_ids: List[int] = [], model_name: str = ""):
        self.workflow_id = workflow_id
        self.submission_ids = submission_ids
        self.model_name = model_name
        self.workflow_results: List[WorkflowResult] = []

    def convert_predictions_for_snapshot(self, predictions: List[dict]):
        reformatted_predictions = []
        for pred in predictions:
            if self._is_not_manually_added_prediction(pred):
                self._remove_unneeded_keys(pred)
                reformatted_predictions.append(pred)
        return reformatted_predictions

    def _is_not_manually_added_prediction(self, prediction: dict) -> bool:
        if isinstance(prediction["start"], int) and isinstance(prediction["end"], int):
            if prediction["end"] > prediction["start"]:
                return True
        return False

    def get_workflow_predictions(self, workflow_api: Workflow):
        submissions = workflow_api.get_complete_submission_objects(self.workflow_id, self.submission_ids)
        wf_results = workflow_api._get_submission_results(submissions)
        predictions = [self._get_reviewed_predictions(result) for result in wf_results]
        texts = [workflow_api.get_ondoc_ocr_from_etl_url(wf["etl_output"]).full_text for wf in wf_results]
        filenames = [sub.input_filename for sub in submissions]
        for preds, text, filename in zip(predictions, texts, filenames):
            yield WorkflowResult(preds, text, filename)

    def _get_reviewed_predictions(self, wf_result: dict):
        results = wf_result["results"]["document"]["results"]
        model_names = list(results.keys())
        if self.model_name:
            self._check_is_valid_model_name(model_names)
        elif len(model_names) > 1:
            raise Exception(f"Multiple models available, you must set self.model_name to one of {model_names}")
        else:
            self.model_name = model_names[0]
        return results[self.model_name]["final"]

    def _check_is_valid_model_name(self, model_names: List[str]) -> bool:
        if self.model_name not in model_names:
            raise Exception(f"{self.model_name} is an available model name. Options: {model_names}")

    def _remove_unneeded_keys(self, prediction: dict):
        for key_to_remove in self._keys_to_remove_from_prediction:
            prediction.pop(key_to_remove, None)

    
@dataclass
class WorkflowResult:
    predictions: List[dict]
    text: str
    filename: str
