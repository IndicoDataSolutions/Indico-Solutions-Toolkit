import tempfile
import shutil
import os
from time import sleep
from typing import List

from indico.queries import (
    CreateDataset,
    CreateWorkflow,
    NewLabelsetArguments,
    AddModelGroupComponent,
    GetWorkflow,
    AddLinkClassificationComponent,
    GetDataset,
)
from indico.types import (
    OcrEngine,
    OmnipageOcrOptionsInput,
    ReadApiOcrOptionsInput,
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
    ):
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
            ocr_settings: ReadApiOcrOptionsInput = read_api_settings
            self.dataset = self.client.call(
                CreateDataset(
                    dataset_name,
                    files=files_to_upload,
                    dataset_type="DOCUMENT",
                    ocr_engine=ocr_engine,
                    read_api_ocr_options=ocr_settings,
                )
            )
        else:
            omnipage_settings["table_read_order"] = (
                TableReadOrder.ROW
                if omnipage_settings["table_read_order"] == "row"
                else TableReadOrder.COLUMN
            )
            ocr_settings: OmnipageOcrOptionsInput = omnipage_settings
            self.dataset = self.client.call(
                CreateDataset(
                    dataset_name,
                    files=files_to_upload,
                    dataset_type="DOCUMENT",
                    ocr_engine=ocr_engine,
                    omnipage_ocr_options=ocr_settings,
                )
            )

    def create_duplicate_dataset(
        self,
        dataset_name: str,
        file_path: str,
        times_to_copy_files=55,
        read_api=True,
        **kwargs,
    ):
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

    def create_workflow(self, name: str, dataset_id: int = None):
        if not self.dataset and not dataset_id:
            raise ToolkitInputError(
                "This call requires a dataset object when instatiating Structure or a provided dataset_id"
            )

        if not dataset_id:
            dataset_id = self.dataset.id

        self.workflow = self.client.call(
            CreateWorkflow(name=name, dataset_id=dataset_id)
        )
        self.workflow_id = self.workflow.id
        self.ocr_id = self.workflow.component_by_type("INPUT_OCR_EXTRACTION").id
        sleep(2)

    def add_teach_task(
        self,
        task_name: str,
        labelset_name: str,
        target_names: List[str],
        model_type=ModelTaskType.ANNOTATION,
        previous_component_id: int = None,
        data_column: str = "document",
        dataset_id: int = None,
        workflow_id: int = None,
    ) -> None:
        """
        Args:
            task_name (str): _description_
            labelset_name (str): _description_
            target_names (List[str]): _description_
            model_type (_type_, optional): _description_. Defaults to ModelTaskType.ANNOTATION.
            previous_component_id (int, optional): _description_. Defaults to None.
            data_column (str, optional): _description_. Defaults to "document".
            dataset_id (int, optional): _description_. Defaults to None.
            workflow_id (int, optional): _description_. Defaults to None.

        Raises:
            Exception: _description_
        """
        prev_comp_id = previous_component_id if previous_component_id else self.ocr_id
        if (
            (not self.dataset and not dataset_id)
            or not prev_comp_id
            or (not self.workflow and not workflow_id)
        ):
            raise Exception(
                "Must have dataset, workflow and** either previous component ID or ocr ID"
            )
        column_id = self.dataset.datacolumn_by_name(data_column).id
        new_labelset = NewLabelsetArguments(
            labelset_name,
            datacolumn_id=column_id,
            task_type=model_type,
            target_names=target_names,
        )

        self.workflow = self.client.call(
            AddModelGroupComponent(
                workflow_id=workflow_id,
                name=task_name,
                dataset_id=dataset_id,
                source_column_id=column_id,
                after_component_id=prev_comp_id,
                new_labelset_args=new_labelset,
            )
        )
        self.last_component_id = self.workflow.components[-1].id
        self.last_questionnaire_id = self.workflow.model_group_by_name(
            task_name
        ).model_group.questionnaire_id
        print(f"Component Added with Teach ID:{self.last_questionnaire_id} ")
        sleep(3)
    
    def add_class_filter(
        self, classes_to_filter: List[str], classification_task_name: str
    ):
        if not self.last_component_id or not self.workflow:
            raise Exception(
                "Need to have a last component ID for classification model and workflow obj"
            )
        filtered = AddLinkClassificationComponent(
            workflow_id=self.workflow.id,
            after_component_id=self.last_component_id,
            model_group_id=self.workflow.model_group_by_name(
                classification_task_name
            ).model_group.id,
            filtered_classes=[classes_to_filter],
            labels="actual",
        )
        self.workflow = self.client.call(filtered)
        print("Added class filter")
