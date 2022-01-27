import datetime
import io
import json
import random
from typing import Dict, List, Set, Tuple, Union, NewType
import uuid

from indico import IndicoClient
from indico.filters import DocumentReportFilter
from indico.queries.datasets import AddFiles, GetDataset, ProcessFiles
from indico.queries.document_report import GetDocumentReport
from indico.queries.questionnaire import AddLabels, GetQuestionnaire, GetQuestionnaireExamples
from indico.queries.workflow import AddDataToWorkflow
import pandas as pd
from PIL import Image

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
        self.client = client

        # Document, text and labels/predictions from review
        self._local_doc_paths: List[str] = []
        self._document_texts: List[str] = []
        self._workflow_results: List[WorkflowResult] = []

        # Text and labels from review after filtering and sampling
        self._filtered_review_labels: List[List[Label]] = []
        self._sampled_doc_paths: List[str] = []
        self._sampled_text: List[str] = []
        self._sampled_review_labels: List[List[Label]] = []

        self._snap_formatted_predictions: List[List[dict]] = []
        self._filenames: List[str] = []

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
        response = self.graphQL_request(graphql_query=query, variables={"id": dataset_id})
        dataset_details = response.get("dataset")
        if not dataset_details:
            raise ValueError(f"No dataset found for id={dataset_id}")

        return dataset_details

    def get_review_data(self, workflow_id: int, update_date: datetime):
        """
        TODO Could be preferable to filter data by completedAt timestamp instead
         of updatedAt, but that is more complex

        Will also run pre review and post review comparisons here and
        add TP/FP/FN metadata as well

        Args:
            workflow_id: ID of production workflow with review enabled
            update_date: Update date for dataset in dev. Used to only capture
                submissions that have been updated since then
        """
        # Get list of submission IDs using GetDocumentReport query
        submission_ids = []
        document_filter = DocumentReportFilter(
            # TODO Comment back in when latest version of the client has been deployed
            # status="COMPLETED",
            workflow_id=workflow_id,
            updated_at_start_date=update_date,
            updated_at_end_date=datetime.datetime.now()
        )
        for page in self.client.paginate(GetDocumentReport(filters=document_filter)):
            for submissions in page:
                submission_ids.extend([sub.submission_id for sub in submissions.input_files])

        # Fetch results from submission IDs
        self._workflow_results = self.get_submission_results_from_ids(
            submission_ids=submission_ids, ignore_deleted_submissions=True,
        )

    def get_submission_full_text(self):
        """
        Fetch full text (OCR) from all workflow submissions. Should be run after
        get_review_data()
        """
        for wf_result in self._workflow_results:
            ondoc_result = self.get_ondoc_ocr_from_etl_url(wf_result.etl_url)
            self._document_texts.append(ondoc_result.full_text)

    def get_document_bytes(self):
        """
        For each workflow submission, extract the storage URL of the underlying
        documents, and then fetch the document bytes using the storage URL and
        save them to disk.
        """
        for wf_result in self._workflow_results:
            image_bytes = self.get_img_bytes_from_etl_url(wf_result.etl_url)
            # For each page, convert to PIL image and write out to PDF
            imgs = [Image.open(io.BytesIO(page_bytes)).convert("RGB") for page_bytes in image_bytes]
            img_path = f"/tmp/{str(uuid.uuid1())}.pdf"
            self._local_doc_paths.append(img_path)
            if len(imgs) == 1:
                imgs[0].save(img_path)
            else:
                imgs[0].save(img_path, save_all=True, append_images=imgs[1:])

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
                elif doc_text[label["start"]: label["end"]] == label["text"]:
                    filtered_doc_labels.append(label)
                # Use string search to fix indices
                elif fix_indices:
                    # Search within bounds if fix_indices_offset is not 0
                    if fix_indices_offset:
                        idx_err = len(label["text"]) - (label["end"] - label["start"])
                        offset = fix_indices_offset + max(0, idx_err)
                        new_start = doc_text.find(
                            label["text"], label["start"] - offset, label["end"] + offset
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

    def sample_data(
        self, sample_ratio: float, weigh_errors_flag: bool = False, random_seed: int = 42
    ):
        """
        Method to sample portion of review data prior to adding it to a dataset
        and workflow.

        TODO Handle weigh_errors_flag

        Args:
            sample_ratio: Ratio of review documents to sample
            weigh_errors_flag: Determines how to sample documents. If True,
                sample more heavily from documents with more of a discrepancy
                between pre and post review predictions.
                Else, sample randomly.
            random_seed: Random seed to use when sampling
        """
        num_samples = int(sample_ratio * len(self._document_texts))
        random.seed(random_seed)
        sampled_idxs = random.sample(range(len(self._document_texts)), num_samples)
        for idx in sampled_idxs:
            self._sampled_doc_paths.append(self._local_doc_paths[idx])
            self._sampled_text.append(self._document_texts[idx])
            self._sampled_review_labels.append(self._filtered_review_labels[idx])

    def add_data(self, dataset_id: int, questionnaire_id: int, workflow_id: int):
        """
        Add processed and sampled review data
        """
        # Add files to dataset
        dataset = self.client.call(AddFiles(dataset_id=dataset_id, files=self._sampled_doc_paths))

        # Save mapping of file names to datafile IDs to later associate with labels
        datafile_names_to_ids = {f.name: f.id for f in dataset.files if f.status == "DOWNLOADED"}

        # Process files (run OCR)
        dataset = self.client.call(ProcessFiles(
            dataset_id=dataset_id, datafile_ids=list(datafile_names_to_ids.values()), wait=True
        ))

        # Add data to workflow (and teach task) so that we can add labels
        self.client.call(AddDataToWorkflow(workflow_id=workflow_id, wait=True))

        # Create mapping b/w datafile IDs and labels
        datafile_ids_to_labels = {}
        for path, labels in zip(self._sampled_doc_paths, self._sampled_review_labels):
            file_name = path.split("/")[-1]
            datafile_id = datafile_names_to_ids[file_name]
            datafile_ids_to_labels[datafile_id] = labels

        # Get unlabeled examples (that we just uploaded) from questionnaire
        examples = self.client.call(GetQuestionnaireExamples(
            questionnaire_id=questionnaire_id, num_examples=len(dataset.files)
        ))

        # Get name of questionnaire and then use it to identify teach task labelset ID
        questionnaire = self.client.call(GetQuestionnaire(questionnaire_id=questionnaire_id))
        dataset = self.client.call(GetDataset(id=dataset_id))
        labelset_id = dataset.labelset_by_name(questionnaire.name).id

        # Add labels to questionnaire (teach task)
        labels = []
        for example in examples:
            doc_labels = datafile_ids_to_labels[example.datafile_id]
            label_dict = {
                "rowIndex": example.row_index,
                "target": json.dumps(doc_labels)
            }
            labels.append(label_dict)
        self.client.call(AddLabels(
            labelset_id=labelset_id, dataset_id=dataset_id, labels=labels,
        ))

    def retrain_model(self, model_group_id: int):
        """
        Call train_model_group on existing model group
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
        self.graphQL_request(graphql_query=mutation, variables={"modelGroupId": model_group_id})

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
