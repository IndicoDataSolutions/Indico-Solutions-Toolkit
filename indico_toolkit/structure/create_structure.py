import tempfile
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
from indico_toolkit.indico_wrapper import Datasets
from indico_toolkit.errors import ToolkitInputError, ToolkitInstantiationError

from utils import ModelTaskType


class Structure:
    def __init__(self, client, dataset_id: int = None, workflow_id: int = None):
        self.client = client
        self.dataset = (
            self.client.call(GetDataset(dataset_id))
            if isinstance(dataset_id, int)
            else None
        )
        self.workflow = (
            self.client.call(GetWorkflow(workflow_id))
            if isinstance(workflow_id, int)
            else None
        )
        self.ocr_id = (
            self.workflow.component_by_type("INPUT__OCR_EXTRACTION").id
            if self.workflow
            else None
        )
        self.last_component_id = None
        self.last_questionnaire_id = None

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
        Optional Kwargs:
            auto_rotate (bool): Autorotate documents in dataset. Defaults to True (READAPI/OMNIPAGE)
            single_column (bool): Read documents as a single-column. Defaults to True (READAPI/OMNIPAGE)
            upscale_images (bool): Upscale image quality. Defaults to True (READAPI/OMNIPAGE)
            languages (list): List of language codes expected in the document. Defaults to ["ENG"] (READAPI/OMNIPAGE)
            force_render (bool): Force render option. Defaults to True (OMNIPAGE)
            native_layout (bool): Native layout option. Defaults to False (OMNIPAGE)
            native_pdf (bool): Native PDF option. Defaults to False (OMNIPAGE)
            table_read_order (str): Table read order of the dataset. Defaults to "row". Options available are "row" or "column" (OMNIPAGE)
        """
        read_api_settings = {
            "auto_rotate": True,
            "single_column": True,
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
            if read_api and arg not in read_api_settings.keys():
                raise ToolkitInputError(
                    f"Not acceptable key word argument '{arg}' for ocr type READ_API. List of valid keywords are {[key for key in read_api_settings.keys()]}"
                )
            if not read_api and arg not in omnipage_settings.keys():
                raise ToolkitInputError(
                    f"Not acceptable key word argument '{arg}' for ocr type OMNIPAGE. List of valid keywords are {[key for key in omnipage_settings.keys()]}"
                )
            if not isinstance(kwargs[arg], type(omnipage_settings[arg])):
                raise ToolkitInputError(
                    f"Incorrect keyword argument {kwargs[arg]} of type {type(kwargs[arg])}, expected type {type(omnipage_settings[arg])}"
                )
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

        self.dataset = self.client.call(
            CreateDataset(
                dataset_name,
                files=files_to_upload,
                dataset_type="DOCUMENT",
                ocr_engine=ocr_engine,
                **ocr_settings,
            )
        )
        print(f"Dataset created with id: {self.dataset.id}")
        return self.dataset

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
        Optional Kwargs:
            auto_rotate (bool): Autorotate documents in dataset. Defaults to True (READAPI/OMNIPAGE)
            single_column (bool): Read documents as a single-column. Defaults to True (READAPI/OMNIPAGE)
            upscale_images (bool): Upscale image quality. Defaults to True (READAPI/OMNIPAGE)
            languages (list): List of language codes expected in the document. Defaults to ["ENG"] (READAPI/OMNIPAGE)
            force_render (bool): Force render option. Defaults to True (OMNIPAGE)
            native_layout (bool): Native layout option. Defaults to False (OMNIPAGE)
            native_pdf (bool): Native PDF option. Defaults to False (OMNIPAGE)
            table_read_order (str): Table read order of the dataset. Defaults to "row". Options available are "row" or "column" (OMNIPAGE)
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

    def create_workflow(self, name: str, dataset_id: int = None) -> Workflow:
        """

        Args:
            name (str): Name of the workflow to be created
            dataset_id (int, optional): Dataset ID for the newly created workflow
                uses self.dataset.id if no dataset_id provided.

        Raises:
            ToolkitInputError: If no dataset_id provided and one not found durring class instantiation.
        """
        if not self.dataset and not dataset_id:
            raise ToolkitInputError(
                "This call requires a dataset object when instatiating Structure or a provided dataset_id"
            )
        if dataset_id and not self.dataset:
            self.dataset = self.client.call(GetDataset(dataset_id))
            print(f"Updating class dataset to id: {dataset_id}")

        if not dataset_id and self.dataset:
            dataset_id = self.dataset.id

        self.workflow = self.client.call(
            CreateWorkflow(name=name, dataset_id=dataset_id)
        )
        self.workflow_id = self.workflow.id
        self.ocr_id = self.workflow.component_by_type("INPUT_OCR_EXTRACTION").id
        sleep(2)
        print(f"Workflow created with ID: {self.worfklow.id}")
        return self.workflow

    def add_teach_task(
        self,
        task_name: str,
        labelset_name: str,
        target_names: List[str],
        model_type="annotation",
        previous_component_id: int = None,
        data_column: str = "document",
        dataset_id: int = None,
        workflow_id: int = None,
        **kwargs,
    ) -> None:
        """
        Args:
            task_name (str): Teach task name
            labelset_name (str): Name for created labelset
            target_names (List[str]): List of target (label) names
            model_type (_type_, optional): Defaults to annotation.
                Available model types:
                    classification
                    form_extraction
                    object_detection
                    classification_multiple
                    regression
                    annotation
                    classification_unbundling
            previous_component_id (int, optional): _description_. Defaults to None.
            data_column (str, optional): Defaults to "document".
            dataset_id (int, optional): Dataset ID. Will use self.dataset.id if not provided
            workflow_id (int, optional): Workflow ID. Will use self.workflow.id if not provided.

        Raises:
            ToolkitInputError: If using an incorrect model type. Please view correct model types for options.
            ToolkitInputError: Needs to have a dataset, workflow, and either previous component ID or ocr ID.

        TODO: clean up kwargs to advanced model training options
        """
        model_map = {
            "classification": ModelTaskType.CLASSIFICATION,
            "form_extraction": ModelTaskType.FORM_EXTRACTION,
            "object_detection": ModelTaskType.OBJECT_DETECTION,
            "classification_multiple": ModelTaskType.CLASSIFICATION_MULTIPLE,
            "regression": ModelTaskType.REGRESSION,
            "annotation": ModelTaskType.ANNOTATION,
            "classification_unbundling": ModelTaskType.CLASSIFICATION_UNBUNDLING,
        }
        if model_type not in model_map.keys():
            raise ToolkitInputError(
                f"{model_type} not found. Available options include {[model for model in model_map.keys()]}"
            )

        prev_comp_id = previous_component_id if previous_component_id else self.ocr_id
        if (
            (not self.dataset and not dataset_id)
            or not prev_comp_id
            or (not self.workflow and not workflow_id)
        ):
            raise ToolkitInputError(
                "Must have dataset, workflow and** either previous component ID or ocr ID"
            )

        if dataset_id:
            self.dataset = (
                self.client.call(GetDataset(dataset_id)) if dataset_id else self.dataset
            )
            print(f"Updating current self.dataset with dataset id: {dataset_id}")
        if workflow_id:
            self.workflow = (
                self.client.call(GetWorkflow(workflow_id))
                if workflow_id
                else self.workflow
            )
            print(f"Updating current self.workflow with workflow id: {workflow_id}")

        column_id = self.dataset.datacolumn_by_name(data_column).id
        new_labelset = NewLabelsetArguments(
            labelset_name,
            datacolumn_id=column_id,
            task_type=model_map[model_type],
            target_names=target_names,
        )

        self.workflow = self.client.call(
            AddModelGroupComponent(
                workflow_id=self.workflow.id,
                name=task_name,
                dataset_id=self.dataset.id,
                source_column_id=column_id,
                after_component_id=prev_comp_id,
                new_labelset_args=new_labelset,
                model_training_options=kwargs,
            )
        )
        print(
            f"Newly created teach task with teach_id: {workflow.components[-1].model_group.questionnaire_id}"
        )
        return Workflow
