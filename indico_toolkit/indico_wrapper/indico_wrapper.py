from typing import List
from indico.queries import (
    RetrieveStorageObject,
    GraphQLRequest,
    JobStatus,
    CreateModelGroup,
)
from indico.types import Dataset, ModelGroup
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

    def train_model(
        self,
        dataset: Dataset,
        model_name: str,
        source_col: str,
        target_col: str,
        wait: bool = False,
    ) -> ModelGroup:
        """
        Train an Indico model 
        Args:
            dataset (Dataset): A dataset object (should represent an uploaded CSV dataset)
            model_name (str): the name for your model
            source_col (str): the csv column that contained the text
            target_col (str): the csv column that contained the labels
            wait (bool, optional): Wait for the model to finish training. Defaults to False.

        Returns:
            ModelGroup: Model group object
        """
        return self.client.call(
            CreateModelGroup(
                name=model_name,
                dataset_id=dataset.id,
                source_column_id=dataset.datacolumn_by_name(source_col).id,
                labelset_id=dataset.labelset_by_name(target_col).id,
                wait=wait,
            )
        )

    def get_storage_object(self, storage_url):
        return self.client.call(RetrieveStorageObject(storage_url))

    def get_job_status(self, job_id: int, wait: bool = True):
        return self.client.call(JobStatus(id=job_id, wait=wait))

    def graphQL_request(self, graphql_query: str, variables: dict = None):
        return self.client.call(
            GraphQLRequest(query=graphql_query, variables=variables)
        )
