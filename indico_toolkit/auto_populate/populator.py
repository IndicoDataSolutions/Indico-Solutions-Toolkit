import time
from json import loads
from typing import List, Tuple, Set
from indico import IndicoClient
from indico.types import Workflow
from indico.queries import CreateExport, DownloadExport, GetDataset, GetModelGroup
from indico_toolkit.errors import ToolkitPopulationError
from indico_toolkit.pipelines import FileProcessing
from indico_toolkit.structure.create_structure import Structure


class AutoPopulator:
    def __init__(self, client: IndicoClient):
        """
        Module for manipulating and creating new workflows and teach tasks.

        Args:
            client (IndicoClient): instantiated Indico Client
        """
        self.client = client
        self.structure = Structure(client)
        self.file_paths = []
        self.file_to_class = {}
        self.file_texts = []
        self._fp = FileProcessing()
        self._exceptions = []

    def set_file_paths(
        self,
        directory_path: str,
        accepted_types: Tuple[str] = (
            "pdf",
            "tiff",
            "tif",
            "doc",
            "docx",
            "png",
            "jpg",
        ),
    ) -> None:
        self._fp.get_file_paths_from_dir(
            directory_path, accepted_types=accepted_types, recursive_search=True
        )
        self.file_paths = self._fp.file_paths

    def create_auto_classification_workflow(
        self,
        dataset_name: str,
        workflow_name: str,
        teach_task_name: str,
        labelset_name: str = None,
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
            dataset_name (str): Name of created dataset
            worlflow_name (str): Name of created workflow
            teach_task_name (str): Name of created teach task
            labelset_name (str, optional): Name of created labelset. Defaults to None.
        Returns:
            Workflow: a Workflow object representation of the newly created workflow
        """
        if not labelset_name:
            labelset_name = f"{teach_task_name}_labelset"
        self._set_full_doc_classes()
        # Create empty dataset
        optional_ocr_options = {
            "auto_rotate": False,
            "upscale_images": True,
            "languages": ["ENG"],
        }
        dataset = self.structure.create_dataset(
            dataset_name=dataset_name,
            files_to_upload=self.file_paths,
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
            target_names=list(self.model_classes),
            dataset_id=dataset.id,
            workflow_id=workflow.id,
            model_type="classification",
        )
        teach_task_id = workflow.components[-1].model_group.questionnaire_id
        labelset_id, model_group_id, target_name_map = self._get_teach_task_details(
            teach_task_id
        )
        labels = self._get_classification_labels(model_group_id, target_name_map)
        self.structure.label_teach_task(
            label_set_id=labelset_id, labels=labels, model_group_id=model_group_id
        )
        return workflow

    def copy_workflow(
        self, dataset_id: int, teach_task_id: int, workflow_name: str, labelset_id: int = None
    ) -> Workflow:
        """
        Create duplicate workflow from dataset and corresponding teach task in same Indico platform.
        Args:
            dataset_id (int): The dataset id of the dataset you wish to copy
            teach_task_id (int): The teach task id of the corresponding teach task to the dataset
            workflow_name (string): The name of the newly created workflow
            labelset_id (int, optional): The labelset id of the corresponding labelset to the dataset
        Returns:
            Workflow: a Workflow object representation of the newly created workflow
        """
        dataset = self.client.call(GetDataset(dataset_id))
        # get dataset snapshot
        if not labelset_id:
            export = self.client.call(
                CreateExport(
                    dataset_id=dataset.id,
                    labelset_id=dataset.labelsets[0].id,
                    wait=True
                )
            )
        else:
            export = self.client.call(
                CreateExport(
                    dataset_id=dataset.id, 
                    labelset_id=labelset_id, 
                    wait=True
                )
            )
        csv = self.client.call(DownloadExport(export.id))
        print("Obtained snapshot")

        # create workflow
        workflow = self.structure.create_workflow(
            name=workflow_name, dataset_id=dataset_id
        )
        print("Created workflow")

        _, old_model_group_id, old_target_name_map = self._get_teach_task_details(
            teach_task_id=teach_task_id
        )
        target_names = list(old_target_name_map.keys())
        old_model_group = self.client.call(
            GetModelGroup(id=old_model_group_id, wait=True)
        )
        model_type = old_model_group.task_type.lower()
        # Create new teach task
        workflow = self.structure.add_teach_task(
            task_name=workflow_name,
            labelset_name=workflow_name,
            target_names=target_names,
            dataset_id=dataset.id,
            workflow_id=workflow.id,
            model_type=model_type,
        )
        # Get labels for new teach task
        (
            new_labelset_id,
            new_model_group_id,
            new_target_name_map,
        ) = self._get_teach_task_details(
            workflow.components[-1].model_group.questionnaire_id
        )
        labels = self._get_labels(
            old_model_group.id, new_model_group_id, csv, new_target_name_map
        )
        # Label new teach task
        result = self.structure.label_teach_task(
            label_set_id=new_labelset_id,
            labels=labels,
            model_group_id=new_model_group_id,
        )
        if result["submitLabelsV2"]["success"] == False:
            raise ToolkitPopulationError("Error: Failed to submit labels")
        return workflow

    def _get_labels(
        self,
        old_model_group_id: int,
        new_model_group_id: int,
        export_csv,
        new_target_name_map: dict,
    ):
        labels = []
        # Retrieve examples and match against filename
        old_examples = self.structure.get_example_ids(
            model_group_id=old_model_group_id, limit=1000
        )
        time.sleep(5)
        new_examples = self.structure.get_example_ids(
            model_group_id=new_model_group_id, limit=1000
        )
        old_examples = {
            i["datafile"]["name"]: i["id"]
            for i in old_examples["modelGroup"]["pagedExamples"]["examples"]
        }
        new_examples = {
            i["datafile"]["name"]: i["id"]
            for i in new_examples["modelGroup"]["pagedExamples"]["examples"]
        }
        old_to_new = {}
        for key, val in old_examples.items():
            if new_examples.get(key):
                old_to_new[val] = new_examples[key]
        # Get labels with new example id and old example targets
        for _, row in export_csv.iterrows():
            if isinstance(row[2], float):
                continue
            old_example_id = row[0]
            targets_list = loads(row[2])
            targets_list = self._convert_label(targets_list, new_target_name_map)
            labels.append(
                {"exampleId": old_to_new[old_example_id], "targets": targets_list}
            )
        return labels
    
    def _get_classification_labels(self, model_group_id: int, target_name_map: dict, labels_to_drop: List[str] = None):
        examples = self.structure.get_example_ids(model_group_id)
        labels = []
        if labels_to_drop is None:
            labels = [
                {"exampleId": ex_id, "targets": [{"clsId": target_name_map[self.file_to_class[examples[ex_id]]]}]} for ex_id in examples.keys()
            ]
        else:
            labels = [
                {"exampleId": ex_id, "targets": [{"clsId": target_name_map[self.file_to_class[examples[ex_id]]]}]} for ex_id in examples.keys() if self.file_to_class[examples[ex_id]] not in labels_to_drop
            ]
        return labels        

    def _convert_label(self, label, target_name_map) -> List[dict]:
        updated_labels = []
        for target in label["targets"]:
            updated_spans = []
            if not target.get("spans"):
                updated_label = {
                    "clsId": target_name_map[target["label"]]
                }
            else:
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

    def _set_full_doc_classes(self):
        self.file_to_class = dict(
            zip(
                [self._fp.file_name_from_path(f) for f in self._fp.file_paths],
                self._fp.parent_directory_of_filepaths,
            )
        )
        self._check_class_minimum()

    def _check_class_minimum(self) -> None:
        if len(self.model_classes) < 2:
            raise ToolkitPopulationError(
                f"You must have documents in at least 2 directories, you only have {self.model_classes}"
            )

    @property
    def model_classes(self) -> Set[str]:
        return set(self.file_to_class.values())
