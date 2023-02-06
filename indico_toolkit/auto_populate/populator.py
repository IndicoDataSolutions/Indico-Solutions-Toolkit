import pandas as pd
from typing import Tuple, Set, List
from indico import IndicoClient
from indico_toolkit.indico_wrapper import Datasets, Workflow, Teach
from indico_toolkit.pipelines import FileProcessing

from .queries import GetExampleIds, GetTeachDetails, LabelTeachTask

class AutoPopulator:
    def __init__(self, client: IndicoClient, directory_path: str):
        """
        Create a CSV of OCR text alongside a class label based on a directory structure.
        You should have a base directory containing sub directories where each directory contains
        a unique file type and only that file type.

        Example::
            base_directory/ -> Instantiate with the page to 'base_directory' as your 'directory_path'
            base_directory/invoices/ -> folder containing only invoices
            base_directory/disclosures/ -> folder containing only disclosures
            etc. etc.

        Args:
            client (IndicoClient): instantiated Indico Client
            directory_path (str): path to a directory containing your filepath structure
        """
        self.client = client
        self.directory_path = directory_path
        self.file_paths = []
        self.file_to_class = {}
        self.file_texts = []
        self._fp = FileProcessing()
        self._exceptions = []

    def set_file_paths(
        self, accepted_types: Tuple[str] = ("pdf", "tiff", "tif", "doc", "docx", "png", "jpg")
    ) -> None:
        self._fp.get_file_paths_from_dir(
            self.directory_path, accepted_types=accepted_types, recursive_search=True
        )
        self.file_paths = self._fp.file_paths

    def create_populator(
        self, verbose: bool = True, catch_exceptions: bool = True
    ):
        """
        Label and train model based on provided file structure
        Args:
            model_type ()
            verbose (bool, optional): Print updates on OCR progress. Defaults to True.
            batch_size (int, optional): Number of files to submit at a time. Defaults to 5.
        """
        self._set_full_doc_classes()
        # Create empty dataset
        datasets = Datasets(self.client)
        dataset = datasets.create_dataset(self.file_paths, "My dataset")
        # Create workflow
        workflows = Workflow(self.client)
        workflow = workflows.create_workflow("My workflow", dataset.id)
        # Add classifier teach task to workflow (should know labels from parent directory)
        teach = Teach(self.client)
        teach_task_id = teach.add_teach_task(
            "My Teach Task",
            "my_labelset_name",
            list(self.model_classes),
            dataset,
            workflow,
        )
        # Retrieve examples and match filename
        labelset_id, model_group_id, target_name_map = self._get_teach_task_details(teach_task_id)
        examples = self._get_examples(model_group_id)
        # Apply labels using Ids mapped in 3
        targets_list = [{"clsId": target_name_map[self.file_to_class[examples[ex_id]]]} for ex_id in examples.keys()] 
        labels = [
            {"exampleId": ex_id, "targets": targets_list} for ex_id in examples.keys()
        ]
        self.client.call(
            LabelTeachTask(
                labelsetId=labelset_id, labels=labels, modelGroupId=model_group_id
            )
        )
    
    def _get_examples(self, modelgroup_id: int):
        examples = self.client.call(
            GetExampleIds(modelGroupId=modelgroup_id, limit=1000)
        )
        return {i["id"] : i["datafile"]["name"] for i in examples["modelGroup"]["pagedExamples"]["examples"]}
    
    def _get_teach_task_details(self, teach_task_id: int):
        teach_task_details = self.client.call(
            GetTeachDetails(teach_task_id=teach_task_id)
        )
        labelset_id = teach_task_details["questionnaire"]["question"]["labelset"]["id"]
        model_group_id = teach_task_details["questionnaire"]["question"]["modelGroupId"]
        target_names = teach_task_details["questionnaire"]["question"]["labelset"][
            "targetNames"
        ]
        target_name_map = {}
        for target in target_names:
            target_name_map[target["name"]] = target["id"]
        return labelset_id, model_group_id, target_name_map

    def _convert_label(self, label, target_name_map) -> List[dict]:
        updated_labels = []
        for target in label["targets"]:
            updated_spans = []
            for span in target["spans"]:
                span["pageNum"] = span["page_num"]
                del span["page_num"]
                updated_spans.append(span)
            updated_label = {
                "clsId": target_name_map[target["label"]],
                "spans": updated_spans,
            }
            updated_labels.append(updated_label)
        return updated_labels
    
    def _set_full_doc_classes(self):
        self.file_to_class = dict(zip([self._fp.file_name_from_path(f) for f in self._fp.file_paths], self._fp.parent_directory_of_filepaths))
        self._check_class_minimum()

    def _check_class_minimum(self) -> None:
        if len(self.model_classes) < 2:
            raise Exception(
                f"You must have documents in at least 2 directories, you only have {self.model_classes}"
            )

    @property
    def model_classes(self) -> Set[str]:
        return set(self.file_to_class.values())