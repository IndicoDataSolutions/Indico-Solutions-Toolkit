import json
import time
from indico import IndicoClient
from indico_toolkit.indico_wrapper import Workflow


class Reviewer(Workflow):
    """
    Class to simulate human reviewer
    """

    def __init__(
        self,
        client: IndicoClient,
        workflow_id: int,
    ):
        self.client = client
        self.workflow_id = workflow_id

    def accept_review(self, submission_id: int, changes: dict) -> None:
        """
        Accept a submission in the review queue
        Args:
            submission_id (int): submission ID
            changes (dict): accepted predictions with format like, e.g. {"model_name": [{"label"...}]}
        """
        self.graphQL_request(
            SUBMIT_REVIEW,
            {
                "rejected": False,
                "submissionId": submission_id,
                "changes": json.dumps(changes),
            },
        )

    def get_random_review_id(self):
        response = self.graphQL_request(
            GET_RANDOM_REVIEW_ID, {"workflowId": self.workflow_id}
        )
        try:
            return response["randomSubmission"]["id"]
        except:
            raise Exception("The review queue is empty")

    def get_random_exception_id(self):
        response = self.graphQL_request(
            GET_RANDOM_EXCEPTION_ID, {"workflowId": self.workflow_id}
        )
        try:
            return response["randomSubmission"]["id"]
        except:
            raise Exception("The exception queue is empty")

    def reject_submission(self, submission_id):
        return self.graphQL_request(
            SUBMIT_REVIEW, {"rejected": True, "submissionId": submission_id}
        )

SUBMIT_REVIEW = """
mutation submitStandardQueue($changes: JSONString, $rejected: Boolean, $submissionId: Int!, $notes: String) {
  submitReview(changes: $changes, rejected: $rejected, submissionId: $submissionId, notes: $notes) {
    id
    __typename
  }
}
"""

GET_RANDOM_EXCEPTION_ID = """
query getExceptionsSubmission($workflowId: Int!) {
  randomSubmission(adminReview: true, workflowId: $workflowId) {
    id
    resultFile
    inputFilename
    autoReview {
      id
      changes
      __typename
    }
    __typename
  }
}
"""

GET_RANDOM_REVIEW_ID = """
query getSubmission($workflowId: Int!) {
  randomSubmission(adminReview: false, workflowId: $workflowId) {
    id
    resultFile
    inputFilename
    autoReview {
      id
      changes
      __typename
    }
    __typename
  }
}
"""
