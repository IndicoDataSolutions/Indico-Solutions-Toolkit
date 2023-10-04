import tempfile
import json
import shutil
import os
from typing import List

from indico.queries import (
    CreateDataset,
    CreateWorkflow,
    NewLabelsetArguments,
    AddModelGroupComponent,
    GetWorkflow,
    GetDataset,
)
from indico.types import (
    OcrEngine,
    Dataset,
    Workflow,
    TableReadOrder,
)
from indico.types import Workflow
from indico_toolkit.errors import ToolkitInputError

from .queries import *
from .utils import ModelTaskType


class Structure:
    def __init__(self, client):
        self.client = client

    def create_dataset(
        self,
        dataset_name: str,
        files_to_upload: List[str],
        read_api: bool = True,
        **kwargs,
    ) -> Dataset:
        """
        Creates a dataset from a list of files.

        Args:
            name_of_dataset (str): Name of the created dataset
            file_path (str): Path of the file to copy.
            read_api (bool, optional): OCR Engine used for the dataset. Defaults to True=READ_API / False=OMNIPAGE
        Kwargs:
            Advanced OCR settings
        """
        read_api_settings = {
            "auto_rotate": True,
            "single_column": False,
            "upscale_images": True,
            "languages": ["ENG"],
        }
        omnipage_settings = {
            **read_api_settings,
            "force_render": True,
            "native_layout": False,
            "native_pdf": False,
            "table_read_order": "row",
        }
        for arg in kwargs.keys():
            if read_api:
                read_api_settings.update({arg: kwargs[arg]})
            else:
                if arg == "table_read_order" and kwargs[arg] not in ["row", "column"]:
                    raise ToolkitInputError(
                        f"Keyword argument {arg} got an unexpected value of {kwargs[arg]}, expected value of either 'row' or 'column'"
                    )
                omnipage_settings.update({arg: kwargs[arg]})

        ocr_engine = OcrEngine.READAPI if read_api else OcrEngine.OMNIPAGE
        if read_api:
            ocr_settings = {"read_api_ocr_options": read_api_settings}
        else:
            omnipage_settings["table_read_order"] = (
                TableReadOrder.ROW
                if omnipage_settings["table_read_order"] == "row"
                else TableReadOrder.COLUMN
            )
            ocr_settings = {"omnipage_ocr_options": omnipage_settings}

        dataset = self.client.call(
            CreateDataset(
                dataset_name,
                files=files_to_upload,
                dataset_type="DOCUMENT",
                ocr_engine=ocr_engine,
                **ocr_settings,
            )
        )
        print(f"Dataset created with ID: {dataset.id}")
        return dataset

    def create_duplicate_dataset(
        self,
        dataset_name: str,
        file_path: str,
        times_to_copy_files=55,
        read_api=True,
        **kwargs,
    ) -> Dataset:
        """
        Creates a dataset w/ duplicate instances of 1 file, historically used to create a spoofed demo.

        Args:
            file_path (str): Path of the file to copy.
            name_of_dataset (str): Name of the created dataset
            times_to_copy_files (int, optional): Amount of times to copy the file. Defaults to 55.
            read_api (bool, optional): OCR Engine used for the dataset. Defaults to True=READ_API / False=OMNIPAGE
        Kwargs:
            Advanced OCR settings
        """
        tempdir = tempfile.TemporaryDirectory()
        try:
            files_to_add = []
            for i in range(times_to_copy_files):
                fpath = os.path.join(tempdir.name, f"sample_{i+1}.pdf")
                shutil.copy(file_path, fpath)
                files_to_add.append(fpath)
            self.create_dataset(
                dataset_name=dataset_name,
                files_to_upload=files_to_add,
                read_api=read_api,
                **kwargs,
            )
        except Exception as e:
            print(e)
        finally:
            tempdir.cleanup()

    def create_workflow(self, name: str, dataset_id: int) -> Workflow:
        """

        Args:
            name (str): Name of the workflow to be created
            dataset_id (int): Dataset ID for the newly created workflow
        """
        workflow = self.client.call(CreateWorkflow(name=name, dataset_id=dataset_id))
        print(f"Workflow created with ID: {workflow.id}")
        return workflow

    def add_teach_task(
        self,
        task_name: str,
        labelset_name: str,
        target_names: List[str],
        dataset_id: int,
        workflow_id: int,
        model_type: str = "annotation",
        data_column: str = "document",
        prev_comp_id: int = None,
        **kwargs,
    ) -> Workflow:
        """
        Args:
            task_name (str): Teach task name
            labelset_name (str): Name for created labelset
            target_names (List[str]): List of target (label) names
            dataset_id (int): Dataset ID.
            workflow_id (int): Workflow ID.
            model_type (str, optional): Defaults to annotation.
                Available model types:
                    classification
                    annotation
                    classification_unbundling
            data_column (str, optional): Defaults to "document".
        Kwargs:
            Advanced model training options
        Returns:
            Updated Workflow with newly added model group component.
        """
        workflow = self.client.call(GetWorkflow(workflow_id))
        dataset = self.client.call(GetDataset(dataset_id))
        model_map = {
            "classification": ModelTaskType.CLASSIFICATION,
            "annotation": ModelTaskType.ANNOTATION,
            "classification_unbundling": ModelTaskType.CLASSIFICATION_UNBUNDLING,
            "classification_multiple": ModelTaskType.CLASSIFICATION_MULTIPLE,
        }
        if model_type not in model_map.keys():
            raise ToolkitInputError(
                f"{model_type} not found. Available options include {[model for model in model_map.keys()]}"
            )
        workflow = self.client.call(GetWorkflow(workflow_id))
        if not prev_comp_id:
            prev_comp_id = workflow.component_by_type("INPUT_OCR_EXTRACTION").id

        column_id = dataset.datacolumn_by_name(data_column).id
        new_labelset = NewLabelsetArguments(
            labelset_name,
            datacolumn_id=column_id,
            task_type=model_map[model_type],
            target_names=target_names,
        )

        workflow = self.client.call(
            AddModelGroupComponent(
                workflow_id=workflow.id,
                name=task_name,
                dataset_id=dataset.id,
                source_column_id=column_id,
                after_component_id=prev_comp_id,
                new_labelset_args=new_labelset,
                model_training_options=json.dumps(kwargs),
            )
        )
        print(
            f"Newly created teach task with teach_id: {workflow.components[-1].model_group.questionnaire_id}"
        )
        return workflow

    def get_teach_details(self, teach_task_id: int):
        return self.client.call(GetTeachDetails(teach_task_id=teach_task_id))

    def get_example_ids(self, model_group_id: int, limit: int):
        return self.client.call(
            GetExampleIds(model_group_id=model_group_id, limit=limit)
        )

    def label_teach_task(self, label_set_id: int, labels: dict, model_group_id: int):
        return self.client.call(
            LabelTeachTask(
                label_set_id=label_set_id, labels=labels, model_group_id=model_group_id
            )
        )
