from typing import TYPE_CHECKING

from indico.queries import GraphQLRequest  # type: ignore[import-untyped]

if TYPE_CHECKING:
    from typing import Any


class SubmissionIdsPendingAutoReview(GraphQLRequest):  # type: ignore[misc]
    QUERY = """
    query SubmissionIdsPendingAutoReview($workflowIds: [Int]) {
        submissions(
            desc: false
            filters: { status: PENDING_AUTO_REVIEW }
            limit: 1000
            orderBy: ID
            workflowIds: $workflowIds
        ) {
            submissions {
                id
            }
        }
    }
    """

    def __init__(self, workflow_id: int):
        super().__init__(self.QUERY, {"workflowIds": [workflow_id]})

    def process_response(self, response: "Any") -> set[int]:
        response = super().process_response(response)
        return {
            submission["id"] for submission in response["submissions"]["submissions"]
        }


class SubmissionIdsPendingDownstream(GraphQLRequest):  # type: ignore[misc]
    QUERY = """
    query SubmissionIdsPendingDownstream($workflowIds: [Int]) {
        submissions(
            desc: false
            filters: {
                AND: {
                    retrieved: false
                    OR: [
                        { status: COMPLETE }
                        { status: FAILED }
                    ]
                }
            }
            limit: 1000
            orderBy: ID
            workflowIds: $workflowIds
        ) {
            submissions {
                id
            }
        }
    }
    """

    def __init__(self, workflow_id: int):
        super().__init__(self.QUERY, {"workflowIds": [workflow_id]})

    def process_response(self, response: "Any") -> set[int]:
        response = super().process_response(response)
        return {
            submission["id"] for submission in response["submissions"]["submissions"]
        }
