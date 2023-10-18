from typing import List

import pandas as pd

from indico import IndicoClient
from indico.queries import AddDatasetFiles

from indico_toolkit.indico_wrapper import Workflow
from indico_toolkit.types import WorkflowResult
from indico_toolkit.auto_populate import AutoPopulator
from indico_toolkit.errors import ToolkitStaggeredLoopError

from .queries import GetDatasetDetails


class StaggeredLoopRecruiter:
    """
    Example:
        wflow = Workflow(client)
        staggered_loop = StaggeredLoopRecruiter(client, "My Model")
        results = wflow.get_submission_results_from_ids([1,2,3])
        # Get CSV containing performance analysis for field "Test Field"
        staggered_loop.get_field_performance(results, "Test Field")
        # Inject submissions from ids [1,2,3] into teach task with dataset, workflow, and teach id of 1.
        staggered_loop.inject_results(dev_client, 1, 1, 1, ["file_1.pdf", "file_2.pdf", "file_3.pdf"], results)
    """

    def __init__(
        self,
        client: IndicoClient,
        model_name: str,
    ):
        self.client = client
        self.wflow = Workflow(client)
        self.model_name = model_name

    def get_field_performance(self, results: List[dict], field: str) -> pd.DataFrame:
        """
        For a given list of Indico results and desired field, return a Pandas DataFrame with an analysis of the results on
        that particular field. Analysis includes:
        - Precision
        - Recall
        - Number of rejected Predictions from pre-review to final
        - Numer of added Predictions from pre-review to final

        Args:
            results (List[dict]): List of raw Indico result JSON
            field (str): The particular label to query for
        Returns:
            pd.DataFrame: A Pandas DataFrame containing analysis of the results
        """
        df = pd.DataFrame()
        for result in results:
            workflow_result = WorkflowResult(result, self.model_name)
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

    def inject_results(
        self,
        dev_client: IndicoClient,
        dataset_id: int,
        workflow_id: int,
        teach_task_id: int,
        files: List[str],
        results: List[dict],
    ):
        """
        For a given list of Indico results and desired fields, inject those results into dev model.

        Args:
            destination_client (IndicoClient): IndicoClient for the target instance to retrain on
            dataset_id (int): The Id of the dataset to retrain on in the same instance as destination_client
            workflow_id (int): The Id of the workflow to retrain on in the same instance as destination_client
            teach_task_id (int): The Id of the teach task to retrain on in the same instance as destination_client
            files (List[str]): List of file paths for corresponding documents you wish to inject labels into
            results (List[dict]): List of raw Indico model results containing label information. 
                NOTE: Result files must all come from a single Indico model.
                NOTE: Files and results must map one-to-one with each other
            field (List[str]): Names of the particular fields to inject labels into
        """
        if len(files) != len(results):
            raise ToolkitStaggeredLoopError(
                "Length of files is not the same as length of results."
            )

        # Convert Indico result into snapshot format and only include fields in kwarg fields
        results = self._convert_results_to_snapshot(results)
        # Map files to targets
        file_to_targets = {}
        for file, result in zip(files, results):
            file_to_targets[file] = result

        # Upload documents to dataset if dataset does not already contain them
        dataset_details = dev_client.call(GetDatasetDetails(dataset_id))
        filenames = [filename["name"] for filename in dataset_details["files"]]
        files_to_upload = [file for file in files if file not in filenames]
        dev_client.call(
            AddDatasetFiles(dataset_id=dataset_id, files=files_to_upload)
        )
        # Inject labels
        populator = AutoPopulator(dev_client)
        populator.inject_labels_into_teach_task(
            workflow_id=workflow_id,
            teach_task_id=teach_task_id,
            file_to_targets=file_to_targets,
        )

    def _convert_results_to_snapshot(results: List[dict]):
        """
        Convert default Indico results into extraction snapshot formats

        Args:
            results (List[dict]): List of default Indico result JSON objects
            fields (List[str], optional): Fields to filter for when converting to snapshot. Defaults to all fields.
        Returns:
            List of results in snapshot format
        """
        new_results = []
        for result in results:
            workflow_result = WorkflowResult(result)
            final_preds = workflow_result.final_predictions
            snapshot_structure = {
                "task_type": "annotation",
                "targets": [],
            }
            for final_pred in final_preds:
                target_structure = {
                    "label": final_pred["label"],
                    "spans": [
                        {
                            "start": final_pred["start"],
                            "end": final_pred["end"],
                            "page_num": final_pred["page_num"],
                        }
                    ],
                    "type": "text",
                }
                snapshot_structure["targets"].append(target_structure)
            new_results.append(snapshot_structure)
        return new_results
