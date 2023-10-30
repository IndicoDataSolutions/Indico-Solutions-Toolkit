import time
import dataclasses
import pandas as pd
from json import loads
from typing import List, Tuple, Dict
from indico import IndicoClient
from indico.types import Workflow
from indico.queries import (
    CreateExport,
    DownloadExport,
    GetDataset,
    GetWorkflow,
    GetModelGroup,
)
from indico_toolkit.errors import ToolkitPopulationError
from indico_toolkit.pipelines import FileProcessing
from indico_toolkit.structure.create_structure import Structure

from .types import *


class AutoPopulator:
    def __init__(self, client: IndicoClient):
        """
        Module for manipulating and creating new workflows and teach tasks.

        Args:
            client (IndicoClient): instantiated Indico Client
        """
        self.client = client
        self.structure = Structure(client)
        self._exceptions = []
        self._fp = FileProcessing()

    def create_auto_classification_workflow(
        self,
        directory_path: str,
        dataset_name: str,
        workflow_name: str,
        teach_task_name: str,
        accepted_types: Tuple[str] = (
            "pdf",
            "tiff",
            "csv",
            "doc",
            "docx",
            "png",
            "jpeg",
            "jpg",
            "pptx",
            "txt",
            "xls",
            "xlsx",
            "rtf"
        ),
    ) -> Workflow:
        """
        Label and train a model based on a directory structure or existing teach task.
        You should have a base directory containing sub directories where each directory contains
        a unique file type and only that file type.

        Example:
            base_directory/ -> Instantiate with the page to 'base_directory' as your 'directory_path'
            base_directory/invoices/ -> folder containing only invoices
            base_directory/disclosures/ -> folder containing only disclosures
            etc. etc.
        Args:
            directory_path (str): Path to a directory containing your filepath structure
            dataset_name (str): Name of created dataset
            worlflow_name (str): Name of created workflow
            teach_task_name (str): Name of created teach task
            accepted_types (Tuple[str], optional): List of accepted file types to search use
        Returns:
            Workflow: a Workflow object representation of the newly created workflow
        """
        self._fp.get_file_paths_from_dir(
            directory_path, accepted_types=accepted_types, recursive_search=True
        )
        file_paths = self._fp.file_paths
        labelset_name = f"{teach_task_name}_labelset"
        file_to_targets = dict(
            zip(
                [self._fp.file_name_from_path(f) for f in self._fp.file_paths],
                [[{"label": parent_directory}] for parent_directory in self._fp.parent_directory_of_filepaths]
            )
        )
        classes = [value[0]["label"] for value in file_to_targets.values()]
        # Create empty dataset
        optional_ocr_options = {
            "auto_rotate": False,
            "upscale_images": True,
            "languages": ["ENG"],
        }
        dataset = self.structure.create_dataset(
            dataset_name=dataset_name,
            files_to_upload=file_paths,
            read_api=True,
            single_column=False,
            **optional_ocr_options,
        )
        # Create workflow
        workflow = self.structure.create_workflow(workflow_name, dataset.id)
        # Add classifier teach task to workflow (should know labels from parent directory)
        workflow = self.structure.add_teach_task(
            task_name=teach_task_name,
            labelset_name=labelset_name,
            target_names=classes,
            dataset_id=dataset.id,
            workflow_id=workflow.id,
            model_type="classification",
        )
        teach_task_id = workflow.components[-1].model_group.questionnaire_id
        labelset_id, model_group_id, target_name_map = self._get_teach_task_details(
            teach_task_id
        )
        if len(classes) < 2:
            raise ToolkitPopulationError(
                f"You must have documents in at least 2 directories, you only have {len(classes)}"
            )
        labels = self.get_labels_by_filename(model_group_id, file_to_targets, target_name_map)
        self.structure.label_teach_task(
            label_set_id=labelset_id, labels=[dataclasses.asdict(label) for label in labels], model_group_id=model_group_id
        )
        return workflow

    def copy_teach_task(
        self,
        dataset_id: int,
        teach_task_id: int,
        workflow_name: str,
        data_column: str = "document",
        rename_labels: Dict[str, str] = None,
        remove_labels: List[str] = None
    ) -> Workflow:
        """
        Create duplicate teach task in same Indico platform.
        Note: Does not work with datasets created with a snapshot
        Args:
            dataset_id (int): The dataset id of the dataset you wish to copy
            teach_task_id (int): The teach task id of the corresponding teach task to the dataset
            workflow_name (string): The name of the newly created workflow
            data_column_id (str, optional): The datacolumn id of the corresponding dataset. Defaults to 'document'
            rename_labels (dict, optional): Dictionary in format {old_label_name : new_label_name} 
            remove_labels (list, optional): List of labels to remove from old teach task
        Returns:
            Workflow: a Workflow object representation of the newly created workflow
        """
        dataset = self.client.call(GetDataset(dataset_id))
        (
            old_labelset_id,
            old_model_group_id,
            old_target_name_map,
        ) = self._get_teach_task_details(teach_task_id=teach_task_id)
        # get dataset snapshot
        export = self.client.call(
            CreateExport(dataset_id=dataset.id, labelset_id=old_labelset_id, wait=True)
        )
        csv = self.client.call(DownloadExport(export.id))
        print("Obtained snapshot")

        # create workflow
        workflow = self.structure.create_workflow(
            name=workflow_name, dataset_id=dataset_id
        )
        time.sleep(2)
        print("Created workflow")
        old_model_group = self.client.call(
            GetModelGroup(id=old_model_group_id, wait=True)
        )
        model_type = old_model_group.task_type.lower()
        # Create new teach task
        workflow = self.structure.add_teach_task(
            task_name=workflow_name,
            labelset_name=workflow_name,
            target_names=list(old_target_name_map.keys()),
            dataset_id=dataset.id,
            workflow_id=workflow.id,
            model_type=model_type,
            data_column=data_column,
        )
        (
            new_labelset_id,
            new_model_group_id,
            new_target_name_map,
        ) = self._get_teach_task_details(
            workflow.components[-1].model_group.questionnaire_id
        )
        # Get file_to_targets from export CSV
        file_to_targets = {}
        for _, row in csv.iterrows():
            # Check for NaN filled rows
            if isinstance(row[2], float):
                continue
            old_example_id = row[0]
            old_examples = self._get_example_list(old_model_group_id)
            targets_list = loads(row[2])["targets"]
            file_to_targets[old_examples.get_example(old_example_id).data_file_name] = targets_list
        labels = self.get_labels_by_filename(
            new_model_group_id,
            file_to_targets,
            new_target_name_map,
            rename_labels,
            remove_labels
        )
        # Label new teach task
        result = self.structure.label_teach_task(
            label_set_id=new_labelset_id,
            labels=[dataclasses.asdict(label) for label in labels],
            model_group_id=new_model_group_id,
        )
        if result["submitLabelsV2"]["success"] == False:
            raise ToolkitPopulationError("Error: Failed to submit labels")
        return workflow

    def inject_labels_into_teach_task(
        self,
        workflow_id: int,
        teach_task_id: int,
        file_to_targets: dict,
        rename_labels: Dict[str, str] = None,
        remove_labels: List[str] = None
    ):
        """
        Add label data into existing teach task

        Args:
            workflow_id (int): Id of the workflow you wish to add labels to
            teach_task_id (int): Id of the corresponding teach task to the workflow
            file_to_targets (dict): mapping of filenames to target label data 
            rename_labels (dict, optional): Dictionary in format {old_label_name : new_label_name} 
            remove_labels (list, optional): List of labels to remove from old teach task
        """
        workflow = GetWorkflow(workflow_id)
        (
            labelset_id,
            model_group_id,
            target_name_map,
        ) = self._get_teach_task_details(
            teach_task_id
        )
        labels = self.get_labels_by_filename(
            model_group_id,
            file_to_targets,
            target_name_map,
            rename_labels,
            remove_labels
        )
        # Label new teach task
        result = self.structure.label_teach_task(
            label_set_id=labelset_id,
            labels=[dataclasses.asdict(label) for label in labels],
            model_group_id=model_group_id,
        )
        if result["submitLabelsV2"]["success"] == False:
            raise ToolkitPopulationError("Error: Failed to submit labels")
    
    def get_labels_by_filename(
        self,
        model_group_id: int,
        file_to_targets: dict,
        target_name_map: dict,
        rename_labels: Dict[str, str] = None,
        remove_labels: List[str] = None
    ) -> List[LabelInput]:
        """
        Args:
            model_group_id (int): ID of the model group to be labeled
            file_to_targets (dict): mapping in the format {filename : targets_list}
            target_name_map (dict): mapping of field name to corresponding target ID
            rename_labels (dict, optional): Dictionary in format {old_label_name : new_label_name} 
            remove_labels (list, optional): List of labels to remove from old teach task
        Returns:
            A list of LabelInput to be ingested by the platform via submitLabelsV2 
        """
        labels = []
        # Retrieve examples and match against filename
        examples = self._get_example_list(model_group_id)

        for filename, targets_list in file_to_targets.items():
            if rename_labels or remove_labels:
                targets_list = self._edit_labels(
                    targets_list, rename_labels, remove_labels
                )
            targets_list = self._convert_label(
                targets_list, target_name_map
            )
            example_id = examples.get_example_id(filename)
            if example_id:
                labels.append(LabelInput(example_id, targets_list))
        return labels

    def _edit_labels(
        self, targets_list: List[dict], rename_labels: Dict[str, str], remove_labels: List[str]
    ):
        new_targets_list = []
        for target in targets_list:
            if remove_labels and target["label"] not in remove_labels:
                if rename_labels and rename_labels.get(target["label"]):
                    target["label"] = rename_labels[target["label"]]
                new_targets_list.append(target)
        return new_targets_list
    
    def _convert_label(
        self, targets_list: List[dict], target_name_map: dict
    ) -> List[LabelInst]:
        updated_labels = []
        for target in targets_list:
            updated_label = LabelInst(target_name_map[target["label"]])
            if target.get("spans"):
                updated_spans = [
                    TokenSpanInput(
                        span["start"], span["end"], span["page_num"]
                    )
                    for span in target["spans"]
                ]
                updated_label.spans = updated_spans
            updated_labels.append(updated_label)
        return updated_labels

    def _get_teach_task_details(self, teach_task_id: int):
        teach_task_details = self.structure.get_teach_details(
            teach_task_id=teach_task_id
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
    
    def _get_example_list(self, model_group_id: int, limit=1000):
        examples = self.structure.get_example_ids(
            model_group_id=model_group_id, limit=limit
        )
        examples = ExampleList(
            examples=[
                Example(i["id"], i["datafile"]["name"])
                for i in examples["modelGroup"]["pagedExamples"]["examples"]
            ]
        )
        return examples