from json import loads
from typing import List, Tuple, Set
from indico import IndicoClient
from indico.queries import CreateExport, DownloadExport, NewLabelsetArguments, AddModelGroupComponent
from indico_toolkit.indico_wrapper import Datasets, Workflow, Teach
from indico_toolkit.pipelines import FileProcessing
from indico_toolkit.types.model_task_type import ModelTaskType

class AutoPopulator:
    def __init__(self, client: IndicoClient, directory_path: str):
        """
        Label and train a model based on a directory structure or existing teach task.
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
        self.datasets = Datasets(client)
        self.workflows = Workflow(client)
        self.teach = Teach(client)
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
        self, 
        dataset_name: str, 
        workflow_name: str, 
        teach_task_name: str,
        labelset_name: str = None
    ):
        """
        Label and train model based on provided file structure
        Args:
            dataset_name (str): Name of created dataset
            worlflow_name (str): Name of created workflow
            teach_task_name (str): Name of created teach task
            labelset_name (str, optional): Name of created labelset. Defaults to None.
        """
        if not labelset_name:
            labelset_name = f"{teach_task_name}_labelset"
        self._set_full_doc_classes()
        # Create empty dataset
        dataset = self.datasets.create_dataset(self.file_paths, dataset_name)
        # Create workflow
        workflow = self.workflows.create_workflow(workflow_name, dataset.id)
        # Add classifier teach task to workflow (should know labels from parent directory)
        teach_task_id = self.teach.add_teach_task(
            teach_task_name,
            labelset_name,
            list(self.model_classes),
            dataset,
            workflow,
        )
        labelset_id, model_group_id, target_name_map = self._get_teach_task_details(self.teach, teach_task_id)
        labels = self.get_labels(self.teach, model_group_id, target_name_map)
        self.teach.label_teach_task(label_set_id=labelset_id, labels=labels, model_group_id=model_group_id)
    
    def copy_workflow(
        self,
        dataset_id: int,
        workflow_name: str
    ):
        """
        Create duplicate workflow in same Indico platform
        """
        # Get snapshot
        dataset = self.datasets.get_dataset(dataset_id)
        export = self.client.call(
            CreateExport(
                dataset_id=dataset_id, 
                labelset_id=dataset.labelsets[0].id,
                wait=True
            )
        )
        csv = self.client.call(DownloadExport(export.id))
        example_ids = csv[csv.keys()[0]].tolist()
        label_col = csv.keys()[len(csv.keys())-1]
        print("got snapshot")
        # create workflow
        workflow = self.workflows.create_workflow(name=workflow_name, dataset_id=dataset_id)
        print("created workflow")
        ocr_id = workflow.component_by_type("INPUT_OCR_EXTRACTION").id
        # Add teach task
        column_id = dataset.datacolumn_by_name("document").id
        new_labelset = NewLabelsetArguments(
            f"{workflow_name}_labelset",
            datacolumn_id=column_id,
            task_type=ModelTaskType.ANNOTATION,
            target_names=self.get_extraction_label_names(csv, label_col),
        )
        workflow = self.client.call(
            AddModelGroupComponent(
                workflow_id=workflow.id,
                name=workflow_name,
                dataset_id=dataset_id,
                source_column_id=column_id,
                after_component_id=ocr_id,
                new_labelset_args=new_labelset,
            )
        )
        print("created teach task")
        # label teach task
        labelset_id, model_group_id, target_name_map = self.teach.get_teach_details(workflow.model_group_by_name(
                workflow_name
            ).model_group.questionnaire_id)
        example_ids = self._get_example_ids(model_group_id)
        targets_list = self.convert_label(self.get_labels(csv, label_col), target_name_map)
        labels = [
            {"exampleId": ex_id, "targets": targets_list} for ex_id in example_ids
        ]
        self.teach.label_teach_task(label_set_id=labelset_id, labels=labels, model_group_id=model_group_id)


    def get_extraction_label_names(self, csv: dict, label_col: str):
        """
        Return a list of all labeled classes in an extraction snapshot.
        """
        label_dict = csv[label_col][0]
        label_dict = loads(label_dict)
        label_set = set()
        for label in label_dict["targets"]:
            label_set.add(label["label"].strip())
        return sorted(list(label_set))

    def get_labels(self, teach: Teach, model_group_id: int, target_name_map: dict, labels_to_drop: List[str] = None):
        # Retrieve examples and match filename
        examples = self._get_examples(teach, model_group_id)
        # Apply labels using target_name_map
        if labels_to_drop is None:
            labels = [
                {"exampleId": ex_id, "targets": [{"clsId": target_name_map[self.file_to_class[examples[ex_id]]]}]} for ex_id in examples.keys()
            ]
        else:
            labels = [
                {"exampleId": ex_id, "targets": [{"clsId": target_name_map[self.file_to_class[examples[ex_id]]]}]} for ex_id in examples.keys() if self.file_to_class[examples[ex_id]] not in labels_to_drop
            ]
        return labels

    def _get_examples(self, teach: Teach, modelgroup_id: int):
        examples = teach.get_example_ids(model_group_id=modelgroup_id, limit=1000)
        return {i["id"] : i["datafile"]["name"] for i in examples["modelGroup"]["pagedExamples"]["examples"]}
    
    def _get_teach_task_details(self, teach: Teach, teach_task_id: int):
        teach_task_details = teach.get_teach_details(teach_task_id=teach_task_id)
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