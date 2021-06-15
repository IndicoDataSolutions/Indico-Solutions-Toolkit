from typing import List
from functools import wraps
import pandas as pd
import time

from indico.client.client import IndicoClient
from indico_toolkit.indico_wrapper import Datasets
from indico_toolkit.types import TeachTask
from indico_toolkit import ToolkitInputError

# TODO: Add processor support on duplicate_teach_task

def task_id_required(fn):
    """
    'Teach' optionally requires an ID on instantiation. For methods that require that it exists,
    throw a runtimeError if 'task_id' not set.
    """

    @wraps(fn)
    def check_task_id(self, *args, **kwargs):
        if not isinstance(self.task_id, int):
            raise RuntimeError(
                "You must set the 'task_id' attribute to use this method"
            )
        return fn(self, *args, **kwargs)

    return check_task_id


class Teach(Datasets):
    """
    Class to create, delete, and manipulate teach tasks
    """

    def __init__(self, client: IndicoClient, dataset_id: int, task_id: int = None):
        super().__init__(client, dataset_id)
        self.dataset = self.get_dataset()
        self.task_id = task_id
        self.df: pd.DataFrame

    def create_teach_task(
        self,
        task_name: str,
        classes: List[str],
        question: str,
        datacolumn_name: str = "text",
        task_type: str = "ANNOTATION",
        processors: List[dict] = [],
        data_type: str = "TEXT",
        num_labelers_required: int = 1,
        keywords: List[str] = [],
        wait: bool = True
    ):
        """
        Create a teach task
        Args:
            task_name (str): Name of teach task
            classes (List[str]): Desired labels for the teach task
            question (str): Question or prompt for labelers
            datacolumn_name (str): Name of source column in dataset. Defaults to "text"
            task_type (str): Teach task type i.e. "CLASSIFICATION", "CLASSIFICATION_MULTIPLE". Defaults to "ANNOTATION"
            processors (List[dict]): Processors to include on teach task. Defaults to []
            data_type (str): Type of data in dataset. Defaults to "TEXT"
            num_labelers_required (int): Number of labelers required for each document. Defaults to 1
            keywords (List[str]): Keywords to help with labeling. Defaults to []
            wait (bool, optional): Wait for teach task to complete
        """
        source_col_id = self.dataset.datacolumn_by_name(datacolumn_name).id
        variables = {
            "name": task_name,
            "processors": processors,
            "dataType": data_type,
            "datasetId": self.dataset.id,
            "numLabelersRequired": num_labelers_required,
            "sourceColumnId": source_col_id,
            "questions": [
                {
                    "type": task_type,
                    "targets": classes,
                    "keywords": keywords,
                    "text": question,
                }
            ],
        }
        teach_task = self.graphQL_request(CREATE_TEACH_TASK, variables)
        self.task_id = teach_task["createQuestionnaire"]["id"]
        if wait:
            self._wait_for_teach_task()


    @task_id_required
    def _wait_for_teach_task(self):
        while self.task.question_status == "STARTED":
            time.sleep(2)


    @task_id_required
    def duplicate_teach_task(
        self,
        task_name: str = None,
        question: str = None,
        wait: bool = True
    ):
        teach_task = self.task
        if not task_name:
            task_name = teach_task.name + " Copy"
        if not question:
            question = teach_task.question
        self.create_teach_task(
            task_name=task_name,
            classes=teach_task.labels,
            question=question,
            datacolumn_name=self.get_col_name_by_id(teach_task.source_column_id),
            task_type=teach_task.task_type,
            data_type=teach_task.data_type,
            num_labelers_required=teach_task.num_labelers_required,
            keywords=teach_task.keywords,
            wait=wait
        )

    @task_id_required
    def label_teach_task(
        self,
        path_to_snapshot: str = None,
        label_col: str = None,
        row_index_col: str = None,
    ) -> dict:
        """
        Label current teach task using snapshot csv or dataset export
        Args:
            path_to_snapshot (str, optional): path to snapshot csv for labeling teach task, if not provided a dataset export is created and used
            label_col (str, optional): column name of label information, inferred if not provided
            row_index_col (str, optional): column name of index column, assumed default format if not provided
        """
        if path_to_snapshot:
            self.df = pd.read_csv(path_to_snapshot)
        else:
            self.df = self.download_export()
        if not row_index_col:
            row_index_col = f"row_index_{self.dataset_id}"
        if not label_col:
            label_col = self._infer_label_col()
        self._check_if_cols_present([row_index_col, label_col])
        labels = []
        clean_df = self.df.dropna(subset=[label_col])
        for _, row in clean_df.iterrows():
            row_index = row[row_index_col]
            target = row[label_col]
            labels.append({"rowIndex": row_index, "target": target})
        variables = {
            "datasetId": self.dataset_id,
            "labelsetId": self.task.labelset_id,
            "labels": labels,
            "modelGroupId": self.task.model_group_id,
        }
        return self.graphQL_request(
            graphql_query=SUBMIT_QUESTIONNAIRE_EXAMPLE, variables=variables
        )
    
    def _check_if_cols_present(self, cols: list) -> None:
        for col in cols:
            if col not in self.df.columns:
                raise ToolkitInputError(f"{col} column not found. Options: {self.df.columns}")

    def _infer_label_col(self) -> str:
        col_names = []
        for name in self.df.columns:
            if "question" in name:
                col_names.append(name)
        if len(col_names) != 1:
            raise ToolkitInputError(
                f"Label column could not be inferred, please specify label column name using label_col argument. Options: {self.df.columns}"
            )
        return col_names[0]

    @task_id_required
    def delete_teach_task(self):
        variables = {"id": self.task_id}
        return self.graphQL_request(DELETE_TEACH_TASK, variables)

    @task_id_required
    def get_teach_task(self) -> TeachTask:
        variables = {"id": self.task_id}
        teach_task = self.graphQL_request(GET_TEACH_TASK, variables)
        return TeachTask(teach_task)

    @property
    def task(self) -> TeachTask:
        return self.get_teach_task()


DELETE_TEACH_TASK = """
        mutation deleteCrowdlabelQuestionnaire($id: Int!) {
          deleteQuestionnaire(id: $id) {
             success
            __typename
          }
        }
        """


CREATE_TEACH_TASK = """
        mutation createCrowdlabelQuestionnaire($dataType: DataType!, $datasetId: Int!, $name: String!, $numLabelersRequired: Int!, $questions: [QuestionInput]!, $sourceColumnId: Int!, $processors: [InputProcessor]) {
          createQuestionnaire(dataType: $dataType, datasetId: $datasetId, name: $name, numLabelersRequired: $numLabelersRequired, questions: $questions, sourceColumnId: $sourceColumnId, processors: $processors) {
            id
            __typename
          }
        }
        """


GET_TEACH_TASK = """
        query getCrowdlabelQuestionnaire($id: Int!) {
          questionnaires(questionnaireIds: [$id]) {
            questionnaires {
              id
              odl
              name
              questionsStatus
              createdAt
              updatedAt
              active
              datasetId
              dataType
              subsetId
              sourceColumnId
              instructions
              numTotalExamples
              numFullyLabeled
              numLabeledByMe
              role
              processors {
                processorType
                args
              }
              assignedUsers {
                id
                userId
                name
                email
                role
                labelCount
                __typename
              }
              questions {
                id
                targets
                type
                text
                modelGroupId
                keywords
                labelset {
                  id
                  name
                  numLabelersRequired
                  __typename
                }
                __typename
              }
              __typename
            }
            __typename
          }
        }  
    """


SUBMIT_QUESTIONNAIRE_EXAMPLE = """
        mutation submitQuestionnaireExample($labelsetId: Int!, $datasetId: Int!, $labels: [SubmissionLabel]!, $modelGroupId: Int) {
          submitLabels(datasetId: $datasetId, labels: $labels, labelsetId: $labelsetId, modelGroupId: $modelGroupId) {
            success
            __typename
          }
        }
    """
