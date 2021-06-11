from typing import List
import json


class TeachTask:
    def __init__(self, teach_task: dict):
        self.teach_task = teach_task["questionnaires"]["questionnaires"][0]

    @property
    def labels(self) -> List[str]:
        return self.teach_task["questions"][0]["targets"]
    
    @property
    def active(self) -> bool:
        return self.teach_task["active"]

    @property
    def model_group_id(self) -> int:
        return self.teach_task["questions"][0]["modelGroupId"]

    @property
    def labelset_id(self) -> int:
        return self.teach_task["questions"][0]["labelset"]["id"]

    @property
    def name(self) -> str:
        return self.teach_task["name"]

    @property
    def question(self) -> str:
        return self.teach_task["questions"][0]["text"]

    @property
    def task_type(self) -> str:
        return self.teach_task["questions"][0]["type"]

    @property
    def processors(self) -> List[dict]:
        return self.teach_task["processors"]

    @property
    def data_type(self) -> str:
        return self.teach_task["dataType"]

    @property
    def num_labelers_required(self) -> int:
        return self.teach_task["questions"][0]["labelset"]["numLabelersRequired"]

    @property
    def keywords(self) -> List[str]:
        return self.teach_task["questions"][0]["keywords"]

    @property
    def source_column_id(self) -> int:
        return self.teach_task["sourceColumnId"]

    @property
    def id(self) -> int:
        return self.teach_task["id"]

    @property
    def dataset_id(self) -> int:
        return self.teach_task["datasetId"]

    @property
    def num_fully_labeled(self) -> int:
        return self.teach_task["numFullyLabeled"]

    @property
    def num_total_examples(self) -> int:
        return self.teach_task["numTotalExamples"]

    @property
    def assigned_users(self) -> List[dict]:
        return self.teach_task["assignedUsers"]
    
    @property
    def question_status(self) -> str:
        return self.teach_task["questionsStatus"]
