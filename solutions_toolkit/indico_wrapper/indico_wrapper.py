from typing import List
from indico.queries import (
    RetrieveStorageObject,
    SubmissionFilter,
    ListSubmissions,
    SubmitReview,
    GetSubmission,
    WorkflowSubmission,
    WaitForSubmissions,
    SubmissionResult,
    UpdateSubmission,
    GraphQLRequest,
    GetDataset,
    CreateExport,
    DownloadExport,
    Submission,
)
from indico import IndicoClient

# TODO -> add job status calls to this class

class IndicoWrapper:
    """
    Class for shared API functionality
    """

    def __init__(
        self, client: IndicoClient
    ):
        """
        Create indico client with user provided arguments

        args:
            client (IndicoClient): instantiated Indico Client object
        """
        self.client = client

    def get_storage_object(self, storage_url):
        return self.client.call(RetrieveStorageObject(storage_url))

    def graphQL_request(self, graphql_query: str, variables: dict):
        return self.client.call(
            GraphQLRequest(query=graphql_query, variables=variables)
        )
