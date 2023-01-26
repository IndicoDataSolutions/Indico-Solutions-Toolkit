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
)
from indico.types import OcrEngine, OmnipageOcrOptionsInput, ReadApiOcrOptionsInput, TableReadOrder
from indico.types import Workflow
from indico_toolkit.indico_wrapper import Datasets

class Structure:
    def __init__(
        self,
        client,
        path_to_file: str,
        read_api: bool = True,
        single_column: bool = False,
        dataset_id: int = None,
        workflow_id: int = None
    ):
        self.client = client
        self.path_to_file = path_to_file
        self.read_api = read_api
        self.single_column = single_column
        self.dataset = None
        if workflow_id:
            workflow_id = self.client.call(GetWorkflow(workflow_id))
        self.workflow: Workflow = workflow_id
        self.workflow_id = None
        self.ocr_id = None  # for linking to first component
        self.last_component_id = None
        self.last_questionnaire_id = None

    # TODO: remove file copying and integrate with Datasets from wrapper
    def create_dataset(self, name_of_dataset: str, times_to_copy_files=55):
        tempdir = tempfile.TemporaryDirectory()
        try:
            files_to_add = []
            for i in range(times_to_copy_files):
                fpath = os.path.join(tempdir.name, f"sample_{i+1}.pdf")
                shutil.copy(self.path_to_file, fpath)
                files_to_add.append(fpath)
            if self.read_api:
                ocr_engine = OcrEngine.READAPI 
                ocr_settings: ReadApiOcrOptionsInput = {
                    "auto_rotate" : True,
                    "single_column": self.single_column,
                    "upscale_images": False,
                    "languages": ["ENG"]
                }
                self.dataset = self.client.call(
                    CreateDataset(
                        name_of_dataset,
                        files=files_to_add,
                        dataset_type="DOCUMENT",
                        ocr_engine=ocr_engine,
                        read_api_ocr_options=ocr_settings
                    )
                )
            else:
                ocr_engine = OcrEngine.OMNIPAGE
                ocr_settings: OmnipageOcrOptionsInput = {
                    "auto_rotate": True,
                    "single_column": self.single_column,
                    "upscale_images": True,
                    "languages": ["ENG"],
                    "force_render": True,
                    "native_layout": False,
                    "native_pdf": False,
                    "table_read_order": TableReadOrder.ROW
                }
                self.dataset = self.client.call(
                    CreateDataset(
                        name_of_dataset,
                        files=files_to_add,
                        dataset_type="DOCUMENT",
                        ocr_engine=ocr_engine,
                        omnipage_ocr_options=ocr_settings
                    )
                )
            print("Dataset created")
        except Exception as e:
            print(e)
        finally:
            tempdir.cleanup()

    def create_workflow(
        self,
        name: str,
    ):
        if not self.dataset:
            raise Exception("This call requires a dataset object in self.dataset")
        self.workflow = self.client.call(
            CreateWorkflow(name=name, dataset_id=self.dataset.id)
        )
        self.workflow_id = self.workflow.id
        self.ocr_id = self.workflow.component_by_type("INPUT_OCR_EXTRACTION").id
        sleep(2)