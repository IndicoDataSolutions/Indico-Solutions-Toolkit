import json
import time
from indico.queries import (
    GraphQLRequest,
    SubmissionResult,
    RetrieveStorageObject,
)
from solutions_toolkit.indico_wrapper import IndicoWrapper


class Reviewer(IndicoWrapper):
    """
    Class to simulate human reviewer

    Example usage:

        reviewer = Reviewer("app.indico.io", 24, "./myapitoken.txt")

        # reject document in exceptions queue
        
        id_to_reject = reviewer.get_random_exception_id()
        reviewer.reject_submission(id_to_reject)

        # accept submission in review queue without changes

        id_to_accept = reviewer.get_random_review_id()
        wf_result = reviewer.get_workflow_result(id_to_accept)["results"]["document"]["results"]
        changes = {"model_name": wf_results["model_name"]["pre_review"]}
        reviewer.accept_review(id_to_accept, changes)
    """

    def __init__(
        self,
        host_url: str,
        workflow_id: int,
        api_token_path=None,
        api_token=None,
        **kwargs
    ):
        self.workflow_id = workflow_id
        super().__init__(
            host_url, api_token_path=api_token_path, api_token=api_token, **kwargs
        )

    def accept_review(self, submission_id: int, changes: dict) -> None:
        """
        Accept a submission in the review queue
        Args:
            submission_id (int): submission ID
            changes (dict): accepted predictions with format like, e.g. {"model_name": [{"label"...}]}
        """
        self.indico_client.call(
            GraphQLRequest(
                query=SUBMIT_REVIEW,
                variables={
                    "rejected": False,
                    "submissionId": submission_id,
                    "changes": json.dumps(changes),
                },
            )
        )

    def get_random_review_id(self):
        response = self.indico_client.call(
            GraphQLRequest(
                query=GET_RANDOM_REVIEW_ID, variables={"workflowId": self.workflow_id}
            )
        )
        try:
            return response["randomSubmission"]["id"]
        except:
            raise Exception("The review queue is empty")

    def get_random_exception_id(self):
        response = self.indico_client.call(
            GraphQLRequest(
                query=GET_RANDOM_EXCEPTION_ID,
                variables={"workflowId": self.workflow_id},
            )
        )
        try:
            return response["randomSubmission"]["id"]
        except:
            raise Exception("The exception queue is empty")

    def reject_submission(self, submission_id):
        res = self.indico_client.call(
            GraphQLRequest(
                query=SUBMIT_REVIEW,
                variables={"rejected": True, "submissionId": submission_id},
            )
        )

    def get_workflow_result(self, submission_id: int, timeout: int = 300) -> dict:
        job = self.indico_client.call(
            SubmissionResult(submission_id, wait=True, timeout=timeout)
        )
        return self.indico_client.call(RetrieveStorageObject(job.result))


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
