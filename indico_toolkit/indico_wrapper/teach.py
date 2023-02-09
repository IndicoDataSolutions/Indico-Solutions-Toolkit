from typing import List
from indico import IndicoClient
from indico.types import Dataset, Workflow
from indico.types.model_group import ModelTaskType
from indico.queries import (
    AddModelGroupComponent,
    GraphQLRequest,
    NewLabelsetArguments,
)
from indico_toolkit.indico_wrapper import IndicoWrapper

class GetTeachDetails(GraphQLRequest):
    GET_TEACH_DETAILS = """
        query getCrowdlabelQuestionnaire($teach_task_id: Int!) {
            questionnaire(id: $teach_task_id) {
                id
                question {
                    id
                    type
                    text
                    modelGroupId
                    status
                    labelset {
                        id
                        targetNames {
                            id
                            name
                            position
                        }
                    }
                }
            }
        }
    """

    def __init__(self, *, teach_task_id: int):
        super().__init__(
            self.GET_TEACH_DETAILS,
            variables={"teach_task_id": teach_task_id},
        )

    def process_response(self, response):
        return super().process_response(response)

class GetExampleIds(GraphQLRequest):
    GET_EXAMPLES = """
        query getExamplesList($modelGroupId: Int!, $filters: ExampleFilter, $skip: Int, $before: Int, $after: Int, $limit: Int, $desc: Boolean, $orderBy: ExampleOrder) {
          modelGroup(modelGroupId: $modelGroupId) {
            id
            pagedExamples(filters: $filters, skip: $skip, before: $before, after: $after, limit: $limit, desc: $desc, orderBy: $orderBy) {
              examples {
                id
                datarowId
                updatedAt
                status
                datafile {
                    name
                }
              }
              pageInfo {
                startCursor
                endCursor
                hasNextPage
                aggregateCount
              }
            }
          }
        }
    """

    def __init__(self, *, model_group_id: int, limit: int):
        super().__init__(
            self.GET_EXAMPLES,
            variables={"modelGroupId": model_group_id, "limit": limit},
        )

    def process_response(self, response):
        return super().process_response(response)

class LabelTeachTask(GraphQLRequest):
    LABEL_TASK = """
        mutation submitQuestionnaireExample
            ($labelsetId: Int!,
            $labels: [LabelInput]!, 
            $modelGroupId: Int) {
          submitLabelsV2(
          labels: $labels, 
          labelsetId: $labelsetId, 
          modelGroupId: $modelGroupId) {
            success
            __typename
          }
        }
    """

    def __init__(self, *, label_set_id: int, labels, model_group_id: int):
        super().__init__(
            self.LABEL_TASK,
            variables={
                "labelsetId": label_set_id,
                "labels": labels,
                "modelGroupId": model_group_id,
            },
        )

    def process_response(self, response):
        return super().process_response(response)


class Teach(IndicoWrapper):
    def __init__(self, client: IndicoClient):
        self.client = client
    
    def add_teach_task(
        self,
        task_name: str,
        labelset_name: str,
        target_names: List[str],
        dataset: Dataset,
        workflow: Workflow,
        model_type=ModelTaskType.CLASSIFICATION,
        data_column: str = "text",
    ) -> int:
        prev_comp_id = workflow.component_by_type("INPUT_OCR_EXTRACTION").id
        column_id = dataset.datacolumn_by_name(data_column).id
        new_labelset = NewLabelsetArguments(
            labelset_name,
            datacolumn_id=column_id,
            task_type=model_type,
            target_names=target_names,
        )
        workflow = self.client.call(
            AddModelGroupComponent(
                workflow_id=workflow.id,
                name=task_name,
                dataset_id=dataset.id,
                source_column_id=column_id,
                after_component_id=prev_comp_id,
                new_labelset_args=new_labelset
            )
        )
        return workflow.model_group_by_name(
            task_name
        ).model_group.questionnaire_id

    def get_teach_details(self, teach_task_id: int):
        return self.client.call(GetTeachDetails(teach_task_id=teach_task_id))

    def get_example_ids(self, model_group_id: int, limit: int):
        return self.client.call(GetExampleIds(model_group_id=model_group_id, limit=limit))
    
    def label_teach_task(self, label_set_id: int, labels: dict, model_group_id: int):
        return self.client.call(LabelTeachTask(label_set_id=label_set_id, labels=labels, model_group_id=model_group_id))


    