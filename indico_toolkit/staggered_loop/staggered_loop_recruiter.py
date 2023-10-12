from typing import List

import pandas as pd

from indico import IndicoClient

from indico_toolkit.indico_wrapper import Workflow
from indico_toolkit.types import WorkflowResult
from indico_toolkit.auto_populate import AutoPopulator
from indico_toolkit.errors import ToolkitStaggeredLoopError


class StaggeredLoopRecruiter:
    """
    Module to filter out candidates for staggered loop training.

    Precision: TP / (TP + FP)
    Recall: TP / (TP + FN)

    TP = prediction in pre_review and final
    FP = prediction in pre_review but not in final
    FN = prediction in final but not in pre_review
    """

    def __init__(
        self, 
        dev_client: IndicoClient, 
        prod_client: IndicoClient,
        prod_dataset_id: int,
        prod_workflow_id: int,
        prod_teach_task_id: int
    ):
        self.dev_client = dev_client
        self.prod_client = prod_client
        self.prod_dataset_id = prod_dataset_id
        self.prod_workflow_id = prod_workflow_id
        self.prod_teach_task_id = prod_teach_task_id

        self._dev_wflow = Workflow(dev_client)
        self._prod_wflow = Workflow(prod_client)

    def analyze(self, results: List[dict], field: str) -> pd.DataFrame:
        """
        For a given list of Indico results and desired field, return a Pandas DataFrame with an analysis of the results on
        that particular field.

        Args:
            results (List[dict]): List of raw Indico result JSON
            field (str): The particular label to query for
        Returns:
            pd.DataFrame: A Pandas DataFrame containing analysis of the results
        """
        df = pd.DataFrame()
        for result in results:
            workflow_result = WorkflowResult(result)
            if workflow_result.post_reviews_predictions:
                # Get Auto Review predictions
                pre_review_preds = workflow_result.post_reviews_predictions[0]
            else:
                pre_review_preds = workflow_result.pre_review_predictions
            final_preds = workflow_result.final_predictions

            pre_review_pred_dict = pre_review_preds.to_dict_by_label
            final_pred_dict = final_preds.to_dict_by_label

            tp = [
                pred
                for pred in final_pred_dict[field]
                if pred in pre_review_pred_dict[field]
            ]
            # Rejected predictions
            fp = [
                pred
                for pred in pre_review_pred_dict[field]
                if pred not in final_pred_dict[field]
            ]
            # Added predictions
            fn = [
                pred
                for pred in final_pred_dict[field]
                if pred not in pre_review_pred_dict[field]
            ]

            precision = len(tp) / (len(tp) + len(fp))
            recall = len(tp) / (len(tp) + len(fn))

            result_df = pd.DataFrame(
                {
                    "Precision": [precision],
                    "Recall": [recall],
                    "Rejected Predictions": [fp],
                    "Added Predictions": [fn],
                }
            )
            df = pd.concat([df, result_df], axis=0)

        return df

    def retrain(
            self, 
            files: List[str], 
            results: List[dict], 
            field: str
        ):
        """
        For a given list of Indico results and desired field, inject those results into prod model and retrain.

        Args:
            files (List[str]): List of file paths for corresponding documents you wish to inject labels into
            results (List[dict]): List of results containing label information. files and results must map one-to-one with each other
            field (str): Name of the particular field to inject labels into
        """
        if len(files) != len(results):
            raise ToolkitStaggeredLoopError("Length of files is not the same as length of results.")
        
        file_to_targets = {}
        for file, result in zip(files, results):
            file_to_targets[file] = result
        
        # Upload documents to dataset if dataset does not already contain them
        
        # Inject labels
        populator = AutoPopulator(self.prod_client)
        populator.inject_labels_into_teach_task(
            workflow_id=0,
            teach_task_id=0,
            file_to_targets=file_to_targets,
        )
