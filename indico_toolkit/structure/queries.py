from indico.queries import GraphQLRequest

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