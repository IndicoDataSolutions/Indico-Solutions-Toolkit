from typing import List
from indico.queries import RetrieveStorageObject, GraphQLRequest, JobStatus
from indico import IndicoClient


class IndicoWrapper:
    """
    Class for shared API functionality
    """

    def __init__(self, client: IndicoClient):
        """
        Create indico client with user provided arguments

        args:
            client (IndicoClient): instantiated Indico Client object
        """
        self.client = client

    def get_storage_object(self, storage_url):
        return self.client.call(RetrieveStorageObject(storage_url))

    def get_job_status(self, job_id: int, wait: bool = True):
        return self.client.call(JobStatus(id=job_id, wait=wait))

    def graphQL_request(self, graphql_query: str, variables: dict = None):
        return self.client.call(
            GraphQLRequest(query=graphql_query, variables=variables)
        )
