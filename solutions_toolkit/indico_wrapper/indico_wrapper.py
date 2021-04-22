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
from indico import IndicoClient, IndicoConfig


class IndicoWrapper:
    """
    Class to handle all indico api calls
    """

    def __init__(
        self, host_url: str, api_token_path: str = None, api_token: str = None, **kwargs
    ):
        """
        Create indico client with user provided arguments

        args:
            host (str): url of Indico environment
            api_token_path (str): local path to Indico API token
            api_token (str): Indico API token string

        """
        self.host_url = host_url
        self.api_token_path = api_token_path
        self.api_token = api_token

        self.config = {"host": self.host_url}

        if self.api_token_path:
            self.config["api_token_path"] = self.api_token_path

        elif self.api_token:
            self.config["api_token"] = self.api_token

        for arg, value in kwargs.items():
            self.config[arg] = value

        indico_config = IndicoConfig(**self.config)
        self.indico_client = IndicoClient(config=indico_config)

    def get_storage_object(self, storage_url):
        return self.indico_client.call(RetrieveStorageObject(storage_url))

    def graphQL_request(self, graphql_query, variables):
        return self.indico_client.call(
            GraphQLRequest(query=graphql_query, variables=variables)
        )

    def get_related_ids_names(
        self, workflow_id=None, model_group_id=None, dataset_id=None
    ) -> dict:
        """
        Find ids and names associated with a given model group, workflow, or dataset id
        Returns:
        ids (dict): dictionary of related ids and names
        """
        if workflow_id:
            ids = self._get_workflow_related_ids_names(workflow_id)
        elif dataset_id:
            ids = self._get_dataset_related_ids_names(dataset_id)
        elif model_group_id:
            ids = self._get_model_related_ids_names(model_group_id)
        else:
            raise KeyError("Missing workflow_id, model_group_id, or dataset_id")
        return ids

    def _get_workflow_related_ids_names(self, workflow_id: int) -> dict:
        query = """
            query ListWorkflows($datasetIds: [Int], $workflowIds: [Int]) {
                workflows(datasetIds: $datasetIds, workflowIds: $workflowIds) {
                    workflows {
                        id
                        name
                        datasetId
                        reviewableModelGroups {
                            name
                            id
                            selectedModel {
                                id
                            }
                        }
                    }
                }
            }
        """
        res = self.graphQL_request(
            query, {"workflowId": workflow_id}
        )
        return {
            "model_group_id": res.reviewableModelGroups.id,
            "model_group_name": res.reviewableModelGroups.name,
            "selected_model_id": res.reviewableModelGroups.selectedModel.id,
            "dataset_id": res.datasetId,
            "workflow_name": res.name,
            "workflow_id": res.id
        }
    
    def _get_dataset_related_ids_names(self, dataset_id: int) -> dict:
        query =  """
            query GetDataset($id: Int) {
                dataset(id: $id) {
                    id
                    name
                    modelGroups {
                        id
                        name
                        selectedModel { 
                            id
                        }
                    }
                }
            }
        """
        res = self.graphQL_request(
            query, {"datasetId": dataset_id}
        )
        return {
            "model_group_id": res.modelGroups.id,
            "model_group_name": res.modelGroups.name,
            "selected_model_id": res.modelGroups.selectedModel.id,
            "dataset_name": res.name,
            "dataset_id": res.datasetId
        }
    
    def _get_model_related_ids_names(self, model_group_id: int) -> dict:
        query =  """
        query GetModelGroup($id: Int) {
            modelGroups(modelGroupIds: [$id]) {
                    modelGroups {
                    id
                    name
                    datasetId
                    selectedModel {
                        id
                    }
                }
            }
        }
        """
        res = self.graphQL_request(
            query, {"id": model_group_id}
        )
        return {
            "model_group_name": res.modelGroups.name,
            "model_group_id": res.id,
            "selected_model_id": res.selectedModel.id,
            "dataset_id": res.datasetId,
        }
