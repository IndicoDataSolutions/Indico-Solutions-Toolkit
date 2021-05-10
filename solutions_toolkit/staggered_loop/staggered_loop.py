import json
from typing import List
import pandas as pd
from solutions_toolkit.indico_wrapper import Workflow
from solutions_toolkit.types import WorkflowResult


class StaggeredLoop(Workflow):

    _keys_to_remove_from_prediction = ["confidence", "text"]

    def __init__(
        self,
        host_url: str,
        api_token_path: str = None,
        api_token: str = None,
        **kwargs,
    ):
        """
        Gather human reviewed submissions to improve existing model

        Example Usage:
            stagger = StaggeredLoop("app.indico.io", api_token_path="./indico_api_token.txt")
            stagger.get_reviewed_prediction_data(312, [7532, 7612], "Model V1")
            stagger.write_csv("./path/to/output.csv")
        """
        super().__init__(
            host_url, api_token_path=api_token_path, api_token=api_token, **kwargs
        )
        self._workflow_results: List[WorkflowResult] = []
        self._snap_formatted_predictions: List[List[dict]] = []
        self._filenames: List[str] = []
        self._document_texts: List[str] = []

    def get_reviewed_prediction_data(
        self, workflow_id: int, submission_ids: List[int] = None, model_name: str = ""
    ) -> None:
        """
        Retrieve and reformat completed submissions that have been human reviewed

        Args:
            workflow_id (int): Workflow ID from which to retrieve submissions
            submission_ids (List[int], optional): Specific submission IDs to retrieve. Defaults to None.
            model_name (str, optional): Name of model within workflow. Defaults to "".
        """
        self.model_name = model_name
        submissions = self.get_complete_submission_objects(workflow_id, submission_ids)
        self._workflow_results = self.get_submission_results_from_ids(
            [sub.id for sub in submissions]
        )
        self._convert_predictions_to_snapshot_format()
        self._get_submission_full_text()
        self._filenames = [i.input_filename for i in submissions]

    def write_csv(
        self,
        output_path: str,
        text_col_name: str = "text",
        label_col_name: str = "target",
        filename_col_name: str = "filename",
    ):
        df = pd.DataFrame()
        df[filename_col_name] = self._filenames
        df[text_col_name] = self._document_texts
        df[label_col_name] = [json.dumps(i) for i in self._snap_formatted_predictions]
        df.to_csv(output_path, index=False)

    def _get_submission_full_text(self) -> None:
        for wf_result in self._workflow_results:
            ondoc_result = self.get_ondoc_ocr_from_etl_url(wf_result.etl_url)
            self._document_texts.append(ondoc_result.full_text)

    def _convert_predictions_to_snapshot_format(self) -> None:
        for predictions in self._workflow_results:
            predictions = self._get_nested_predictions(predictions)
            predictions = self._reformat_predictions(predictions)
            self._snap_formatted_predictions.append(predictions)

    def _reformat_predictions(self, predictions: List[dict]) -> List[dict]:
        reformatted_predictions = []
        for pred in predictions:
            if self._is_not_manually_added_prediction(pred):
                self._remove_unneeded_keys(pred)
                reformatted_predictions.append(pred)
        return reformatted_predictions

    def _get_nested_predictions(self, wf_result: WorkflowResult) -> List[dict]:
        if self.model_name != "":
            wf_result.model_name=self.model_name
        return wf_result.post_review_predictions

    def _is_not_manually_added_prediction(self, prediction: dict) -> bool:
        if isinstance(prediction["start"], int) and isinstance(prediction["end"], int):
            if prediction["end"] > prediction["start"]:
                return True
        return False

    def _remove_unneeded_keys(self, prediction: dict):
        for key_to_remove in self._keys_to_remove_from_prediction:
            prediction.pop(key_to_remove, None)
