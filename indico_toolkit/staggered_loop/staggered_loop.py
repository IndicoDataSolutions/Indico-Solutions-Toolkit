from datetime import datetime
import json
import random
import warnings
from typing import Dict, List, Union, NewType
from pathlib import Path

from indico import IndicoClient
from indico.filters import DocumentReportFilter
from indico.queries import GetSubmission
from indico.queries.datasets import AddFiles, ProcessFiles
from indico.queries.document_report import GetDocumentReport
from indico.queries.questionnaire import (
    AddLabels,
    GetQuestionnaireExamples,
)
from indico.queries.workflow import AddDataToWorkflow
import pandas as pd

from indico_toolkit.indico_wrapper import Workflow
from indico_toolkit.staggered_loop import metrics
from indico_toolkit.types import WorkflowResult, Predictions


# Create new types for extraction label objects
Label = NewType("label", Dict[str, Union[int, str]])


class StaggeredLoop(Workflow):

    _keys_to_remove = ["confidence", "text"]

    def __init__(self, client: IndicoClient):
        """
        Gather human reviewed submissions to improve existing model

        Example Usage:
            stagger = StaggeredLoop("app.indico.io", api_token_path="./indico_api_token.txt")
            stagger.get_reviewed_prediction_data(312, [7532, 7612], "Model V1")
            stagger.write_csv("./path/to/output.csv")
        """
        warnings.warn("This implementation is deprecated! Use at your own risk!")
        self.client = client

        # Document, text and labels/predictions from review
        self._document_texts: List[str] = []
        self._document_paths: List[str] = []
        self._workflow_results: List[WorkflowResult] = []

        # Text and labels from review after filtering and sampling
        self._filtered_review_labels: List[List[Label]] = []
        self._sampled_doc_paths: List[str] = []
        self._sampled_text: List[str] = []
        self._sampled_review_labels: List[List[Label]] = []

        self._snap_formatted_predictions: List[List[dict]] = []
        self._filenames: List[str] = []

    def set_workflow_results(
        self,
        workflow_results: List[WorkflowResult],
        doc_paths: List[str],
        doc_texts: List[str],
    ) -> None:
        """
        StaggeredLoop functionality typically requires working across multiple
        environments, because users of the platform often use a prod environment
        for workflow submissions, and a dev environment for labeling and training
        models.

        This function will typically be used to set the workflow results fetched
        from one environment (prod) as an attribute of the instance of the class
        for another environment (dev).

        Args:
            workflow_results: Workflow results to set as attribute of instance of class
        """
        self._workflow_results = workflow_results
        self._document_paths = doc_paths
        self._document_texts = doc_texts

    def update_model_settings(self, model_group_id: int, model_training_options: Dict):
        query = """
        mutation UpdateModelGroupSettings(
            $modelGroupId: Int!,
            $modelTrainingOptions: JSONString,
        ) {
            updateModelGroupSettings(
            modelGroupId: $modelGroupId,
            modelTrainingOptions: $modelTrainingOptions
            ) {
                id
                modelOptions {
                    modelTrainingOptions
                }
            }
        }
        """
        res = self.graphQL_request(
            query,
            {
                "modelGroupId": model_group_id,
                "model_training_options": model_training_options,
            },
        )[0]
        return res

    def model_group_details(self, model_group_id: int) -> Dict:
        query = """
            query GetModelGroup($id: Int) {
                modelGroups(modelGroupIds: [$id]) {
                    modelGroups {
                        id
                        name
                        datasetId
                        workflowId
                        questionnaireId
                        labelset {
                            id
                            targetNames {
                                id
                                name
                            }
                        }
                        selectedModel {
                            id
                        }
                    }
                }
            }
        """
        res = self.graphQL_request(query, {"id": model_group_id})["modelGroups"][
            "modelGroups"
        ][0]
        related = {
            "model_group_name": res["name"],
            "model_group_id": model_group_id,
            "selected_model_id": res["selectedModel"]["id"],
            "dataset_id": res["datasetId"],
            "workflow_id": res["workflowId"],
            "labelset_id": res["labelset"]["id"],
            "questionnaire_id": res["questionnaireId"],
            "target_name_to_id": {
                target_name["name"]: target_name["id"]
                for target_name in res["labelset"]["targetNames"]
            },
        }
        return related

    def get_datafile_page_meta(self, datafile_id: int) -> List[Dict]:
        """_summary_

        Args:
            datafile_id (int): ID of datafile

        Returns:
            List[Dict]: Per page metadata for datafile, including start / end offset
        """
        query = """
            query dataFileQuery($datafile:Int!) {
                datafile(datafileId:$datafile) {
                    id
                    rainbowUrl
                    pages {
                        docStartOffset
                        docEndOffset
                    }
                }
            }
        """
        response = self.graphQL_request(
            graphql_query=query, variables={"datafile": datafile_id}
        )
        page_meta = response.get("datafile", {}).get("pages", [])
        return page_meta

    def get_dataset_details(
        self, dataset_id: int
    ) -> Dict[str, Union[int, str, Dict[str, Union[int, str]]]]:
        """
        Find the following for the dataset in dev that we want to add data to
        * datacolumns/labelsets
        * updatedAt timestamp

        Args:
            dataset_id: Dataset ID to fetch details for

        Returns:
            dataset_details: JSON response from graphQL with dataset details

        Raises:
            ValueError: If no dataset details are returned for the supplied dataset_id
        """
        # Custom graphQL query to return updatedAt timestamp in addition to
        # other details about the dataset
        query = """
        query getDataset($id: Int) {
            dataset(id: $id) {
                id
                name
                rowCount
                status
                updatedAt
                datacolumns {
                    id
                    name
                }
                labelsets{
                    id
                    name
                }
            }
        }
        """
        response = self.graphQL_request(
            graphql_query=query, variables={"id": dataset_id}
        )
        dataset_details = response.get("dataset")
        if not dataset_details:
            raise ValueError(f"No dataset found for id={dataset_id}")
        print(f"Fetched dataset metadata dataset_id={dataset_id}")

        return dataset_details

    def get_review_data(
            self, workflow_id: int,
            update_date: datetime,
            selected_submission_ids: List[int] = None,
            reviewer_ids: List[int] = None
    ) -> List[WorkflowResult]:
        """
        Fetch review data from workflow, using the update_date as a filter

        Will also run pre review and post review comparisons here and
        add TP/FP/FN metadata as well

        Args:
            workflow_id: ID of production workflow with review enabled
            update_date: Update date for dataset in dev. Used to only capture
                submissions that have been updated since then
            reviewer_ids: User IDs of specific reviewers. Used to select submissions only
                reviewed by specified reviewers
            selected_submission_ids: Specific submission IDs selected by user to use to retrain model

        Returns:
            workflow_results: Review data fetched from workflow
        """

        if selected_submission_ids:
            submission_ids = selected_submission_ids
        else:
            # Get list of submission IDs using GetDocumentReport query
            submission_ids = []

            # TODO: deal with timezones...
            document_filter = DocumentReportFilter(
                # status="COMPLETE",
                workflow_id=workflow_id,
                updated_at_start_date=update_date,
                updated_at_end_date=datetime.now(),
            )
            if reviewer_ids:
                for page in self.client.paginate(GetDocumentReport(filters=document_filter)):
                    for sub in page:
                        if sub.status == "COMPLETE":
                            submission = self.client.call(GetSubmission(sub.submission_id))
                            for review in submission.reviews:
                                if review.created_by in reviewer_ids:
                                    submission_ids.append(sub.submission_id)
            else:
                for page in self.client.paginate(GetDocumentReport(filters=document_filter)):
                    submission_ids.extend(
                        [sub.submission_id for sub in page if sub.status == "COMPLETE"]
                    )

        # Fetch results from submission IDs
        self._workflow_results = self.get_submission_results_from_ids(
            submission_ids=submission_ids,
            ignore_deleted_submissions=True,
        )
        print(
            f"Downloaded review data from workflow_id={workflow_id} that was updated since"
            f"date={update_date} num_submissions={len(self._workflow_results)}"
        )
        return self._workflow_results

    def get_submission_full_text(self) -> List[str]:
        """
        Fetch full text (OCR) from all workflow submissions. Should be run after
        get_review_data()
        """
        document_texts = []
        for wf_result in self._workflow_results:
            ondoc_result = self.get_ondoc_ocr_from_etl_url(wf_result.etl_url)
            document_texts.append(ondoc_result.full_text)

        print("Downloaded text (OCR) for all workflow submissions")
        self._document_texts = document_texts
        return document_texts

    def get_document_bytes(self) -> List[str]:
        """
        For each workflow submission, extract the storage URL of the underlying
        documents, and then fetch the document bytes using the storage URL and
        save them to disk.
        """
        document_paths = []
        for wf_result in self._workflow_results:
            # TODO: support bundles
            # TODO: don't assume input_file name is unique
            basename = Path(wf_result.result["input_file"]).name
            doc_path = f"/tmp/{basename}"
            doc_bytes = self.get_file_bytes(wf_result.result["input_file"])
            with open(doc_path, "wb") as f:
                f.write(doc_bytes)
            document_paths.append(doc_path)
        print(
            "Downloaded document bytes for all workflow submissions and wrote them to disk"
        )
        return document_paths

    @staticmethod
    def preprocess_review_data(
        text: List[str],
        labels: List[List[Label]],
        no_idx_labels: List[List[Label]] = None,
        fix_indices: bool = True,
        fix_indices_offset: int = 5,
        fix_cls_whitespace: bool = True,
        no_op: bool = False,
    ) -> List[List[Label]]:
        """
        Given text and labels (or model predictions) from review, apply the necessary
        preprocessing steps to make the data usable for training.

        Review data has labels where the start/end indices are incorrect and are not
        aligned with the matching text. If this data is fed directly to a finetune
        SequenceLabeler model, that will result in errors.

        There are also some odd cases where the indices are off by one or a couple
        indices (both start and end). The root cause for this is unclear, but the
        fix_indices logic helps deal with that issue.

        Args:
            text: The text for each document
            labels: The labels (or predictions) for each document
            no_idx_labels: Any labels that have completely missing start/end indices,
                which happens when false negatives are manually keyed into review. If
                this argument is not None, these will be added to the labels (after
                finding the correct indices, if they exist)
            fix_indices: If True, for any labels with incorrect start/end indices,
                search for the label text in the document text to try to find the
                correct text, and correct the start/end indices. If the text is not
                found in the document, that label will be removed. If False, any
                labels with incorrect start/end indices are not used for training.
            fix_indices_offset: Only applicable if fix_indices is True. If set to 0,
                search the entire document to find the indices for labels with
                incorrect start/end indices. If set to an integer, search within bounds
                based on this param. The higher the offset, the more "leeway" you have
                searching the document text. The purpose of this param is to avoid
                searching the entire document text, which is an issue if the text of a
                label appears multiple times within a document, because it is then
                possible to find the wrong start/end indices.
            fix_cls_whitespace: Some label names have extra whitespace at the end. For
                example, the label could sometimes appear as "Invoice Number" and
                elsewhere as "Invoice Number ". If True, remove a single trailing
                whitespace character on any labels with this issue.
            no_op: If True, ignore issues with indices, and keep all labels unless
                excluded based on labels_to_exclude set
        Returns:
            filtered_labels: Labels for each doc after preprocessing has been applied
        """
        filtered_labels = []
        for i in range(len(text)):
            doc_text = text[i]
            doc_labels = labels[i]
            filtered_doc_labels = []
            for label in doc_labels:
                # Fix labels with extra whitespace at end
                if fix_cls_whitespace and label["label"][-1] == " ":
                    label["label"] = label["label"][:-1]
                # Add label regardless of whether indices are right or wrong if no_op flag is True
                elif no_op:
                    filtered_doc_labels.append(label)
                # Labels with correct start/end indices
                elif doc_text[label["start"] : label["end"]] == label["text"]:
                    filtered_doc_labels.append(label)
                # Use string search to fix indices
                elif fix_indices:
                    # Search within bounds if fix_indices_offset is not 0
                    if fix_indices_offset:
                        idx_err = len(label["text"]) - (label["end"] - label["start"])
                        offset = fix_indices_offset + max(0, idx_err)
                        new_start = doc_text.find(
                            label["text"],
                            label["start"] - offset,
                            label["end"] + offset,
                        )
                    # Otherwise search within the entire document
                    else:
                        new_start = doc_text.find(label["text"])
                    # Add label to set of doc labels if the label text was found
                    if new_start != -1:
                        label["start"] = new_start
                        label["end"] = new_start + len(label["text"])
                        filtered_doc_labels.append(label)

            # If no_idx_labels are passed in (and fix_indices is True), add these to
            # the set of doc labels as well.
            # In this case, we search the full document because we have no start/end
            # indices to serve as a frame of reference
            # Note that some labels will not be found in the text, because they were
            # manually added during review but are not actually contained in the
            # document text (or are missing due to an OCR error)
            if no_idx_labels and fix_indices:
                doc_no_idx_labels = no_idx_labels[i]
                for label in doc_no_idx_labels:
                    # Fix labels with extra whitespace at end
                    if fix_cls_whitespace and label["label"][-1] == " ":
                        label["label"] = label["label"][:-1]
                    # Add label regardless of whether indices are right or wrong if no_op flag is True
                    elif no_op:
                        filtered_doc_labels.append(label)
                    # Search for label within the entire document
                    new_start = doc_text.find(label["text"])
                    if new_start != -1:
                        label["start"] = new_start
                        label["end"] = new_start + len(label["text"])
                        filtered_doc_labels.append(label)
            filtered_labels.append(filtered_doc_labels)
        return filtered_labels

    def process_review_data(self):
        """
        Compare data pre and post review, compute TP/FP/FNs, and then generate
        processed_review_data that is ready to be added to a dataset

        TODO
         * Add partial metadata flag when ready
         * Consider building test set of review data as well
         * Store FP/FN counts in metadata for sampling
        """
        # Separate review data with missing start/end indices
        # Also extract predictions from workflow result obj
        normal_review_labels = []
        no_idx_labels = []
        preds = []
        for result in self._workflow_results:
            doc_labels = result.post_review_predictions._preds
            normal_doc_labels = []
            no_idx_doc_labels = []
            for label in doc_labels:
                # If reviewer manually keyed in label, it will be missing
                # start/end indices
                if "start" not in label or "end" not in label:
                    no_idx_doc_labels.append(label)
                else:
                    normal_doc_labels.append(label)
            normal_review_labels.append(normal_doc_labels)
            no_idx_labels.append(no_idx_doc_labels)
            preds.append(result.predictions._preds)

        # Preprocess review data and predictions
        review_labels = self.preprocess_review_data(
            text=self._document_texts,
            labels=normal_review_labels,
            no_idx_labels=no_idx_labels,
        )
        pred_labels = self.preprocess_review_data(
            text=self._document_texts,
            labels=preds,
        )

        # Need the confusion matrix b/w preds and review data for formulating
        # datasets that take specific subsets of false negatives and false positives
        tps, fps, fns = metrics.identify_tps_fps_fns(
            true=review_labels,
            predicted=pred_labels,
            tp_ratio=1,
            fp_ratio=1,
            fn_ratio=1,
        )
        # Add FNs to TPs, and also add FPs that are potential duplicates
        # using their original label
        for doc_text, doc_tps, doc_fns, doc_fps in zip(
            self._document_texts, tps, fns, fps
        ):
            doc_labels = doc_tps + doc_fns
            for fp in doc_fps:
                if any(
                    fp["text"] == tp["text"] and fp["orig_label"] == tp["label"]
                    for tp in doc_tps
                ):
                    # Use original label instead of <PAD> for FP
                    fp["label"] = fp["orig_label"]
                    doc_labels.append(fp)
            self._filtered_review_labels.append(doc_labels)
        print("Processed review data by comparing pre and post review annotations")

    def sample_data(
        self,
        sample_ratio: float,
        oversample_errors: bool = False,
        random_seed: int = 42,
    ):
        """
        Method to sample portion of review data prior to adding it to a dataset
        and workflow.

        TODO Handle oversample_errors

        Args:
            sample_ratio: Ratio of review documents to sample
            oversample_errors: Determines how to sample documents. If True,
                sample more heavily from documents with more of a discrepancy
                between pre and post review predictions.
                Else, sample randomly.
            random_seed: Random seed to use when sampling
        """
        num_samples = int(sample_ratio * len(self._document_texts))
        random.seed(random_seed)
        sampled_idxs = random.sample(range(len(self._document_texts)), num_samples)
        for idx in sampled_idxs:
            self._sampled_doc_paths.append(self._document_paths[idx])
            self._sampled_text.append(self._document_texts[idx])
            self._sampled_review_labels.append(self._filtered_review_labels[idx])
        print(f"Sampled ratio={sample_ratio} of review data")

    def _reformat_labels(self, labels, target_name_to_id):
        result = []
        for label in labels:
            result.append(
                {
                    "clsId": target_name_to_id[label["label"]],
                    "spans": [
                        {
                            "start": label["start"],
                            "end": label["end"],
                            "pageNum": label["pageNum"],
                        }
                    ],
                }
            )
        return result

    def add_data(self, model_group_id: int, partial: bool = True):
        """
        Add processed and sampled review data to dataset and teach task

        TODO: Make it easier to debug in the case of a failure by saving out serialized
         state of instance of class to a file, and allow user to resume progress from
         a specific stage of this method

        Args:
            dataset_id: Dataset ID for dataset to add data to
            questionnaire_id: Questionnaire (teach task) ID associated with dataset
            workflow_id: Workflow ID for workflow associated with dataset and teach task.
                Required for adding data to teach task
        """
        print("Finding related IDs (dataset, workflow, etc.)")
        related = self.model_group_details(model_group_id=model_group_id)
        questionnaire_id = related["questionnaire_id"]
        dataset_id = related["dataset_id"]
        workflow_id = related["workflow_id"]
        labelset_id = related["labelset_id"]
        target_name_to_id = related["target_name_to_id"]

        # Add files to dataset
        print(self._sampled_doc_paths)
        dataset = self.client.call(
            AddFiles(dataset_id=dataset_id, files=self._sampled_doc_paths)
        )

        # Save mapping of file names to dev datafile IDs to later associate with labels
        datafile_names_to_ids = {
            Path(f.name).name: f.id for f in dataset.files if f.status == "DOWNLOADED"
        }
        print("Datafile name to ID map", datafile_names_to_ids)

        print("Processing files...")
        # Process files (run OCR)
        dataset = self.client.call(
            ProcessFiles(
                dataset_id=dataset_id,
                datafile_ids=list(datafile_names_to_ids.values()),
                wait=True,
            )
        )

        # Double check OCR content
        # WARNING: these docs paths / datafile IDs are related to the prod environment
        print(
            "Ensuring text from prod environment lines up with dev environment doc lengths"
        )
        for idx, doc_path in enumerate(self._sampled_doc_paths):
            datafile_id = datafile_names_to_ids[Path(doc_path).name]
            text = self._sampled_text[idx]
            page_meta = self.get_datafile_page_meta(datafile_id)
            assert (
                len(text) == page_meta[-1]["docEndOffset"]
            ), "OCR text does not match -- labels will be misaligned with text"

        # Add data to workflow (and teach task) so that we can add labels
        print("Adding files from dataset to workflow and teach task")
        self.client.call(AddDataToWorkflow(workflow_id=workflow_id, wait=True))

        # Create mapping b/w datafile IDs and labels
        datafile_ids_to_labels = {}
        for path, labels in zip(self._sampled_doc_paths, self._sampled_review_labels):
            file_name = path.split("/")[-1]
            datafile_id = datafile_names_to_ids[Path(file_name).name]
            datafile_ids_to_labels[datafile_id] = labels

        # Get unlabeled examples (that we just uploaded) from questionnaire
        # Add labels to questionnaire (teach task)
        labels = []
        for datafile_id in datafile_ids_to_labels:
            examples = self.client.call(
                GetQuestionnaireExamples(
                    questionnaire_id,
                    datafile_id=datafile_id,
                    # Arbitrarily high
                    num_examples=1000,
                )
            )

            for example in examples:
                doc_labels = datafile_ids_to_labels[example.datafile_id]
                label_dict = {
                    "exampleId": example.id,
                    # This imposes some constraits on input format?
                    "targets": self._reformat_labels(doc_labels, target_name_to_id),
                    "partial": partial,
                    "override": True,
                    "rejected": False,
                }
                labels.append(label_dict)

        if not labels:
            raise AssertionError("No new labels added -- aborting.")

        self.client.call(
            AddLabels(
                labelset_id=labelset_id,
                model_group_id=model_group_id,
                labels=labels,
            )
        )
        print(f"Added {len(labels)} labels to examples newly added to teach task")

    def retrain_model(self, model_group_id: int):
        """
        Call train_model_group on existing model group

        Arg:
            model_group_id: ID of model group to retrain
        """
        mutation = """
        mutation (
            $modelGroupId: Int!,
        ){
            retrainModelGroup(
                modelGroupId: $modelGroupId,
                forceRetrain: true
            )
            {
                id
            }
        }
        """
        res = self.graphQL_request(
            graphql_query=mutation, variables={"modelGroupId": model_group_id}
        )
        print("Retraining extraction model with new review data")

    # ORIGINAL STAGGERED LOOP FUNCTIONALITY. NO LONGER USED FOR PARTIAL LABELS
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
        self.get_submission_full_text()
        self._filenames = [i.input_filename for i in submissions]

    def to_csv(
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

    def _convert_predictions_to_snapshot_format(self) -> None:
        for predictions in self._workflow_results:
            predictions = self._get_nested_predictions(predictions)
            predictions = self._reformat_predictions(predictions)
            self._snap_formatted_predictions.append(predictions)

    def _reformat_predictions(self, predictions: Predictions) -> List[dict]:
        predictions.remove_human_added_predictions()
        predictions.remove_keys(self._keys_to_remove)
        return predictions.to_list()

    def _get_nested_predictions(self, wf_result: WorkflowResult) -> Predictions:
        if self.model_name != "":
            wf_result.model_name = self.model_name
        return wf_result.post_review_predictions
