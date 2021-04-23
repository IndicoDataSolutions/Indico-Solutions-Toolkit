from indico.queries import ListWorkflows

from solutions_toolkit.indico_wrapper import IndicoWrapper


class FindRelated(IndicoWrapper):

    _detailed_list_wf_query = """
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

    def __init__(self, host_url, api_token_path=None, api_token=None, **kwargs):
        super().__init__(
            host_url, api_token_path=api_token_path, api_token=api_token, **kwargs
        )

    def workflow_id(self, workflow_id: int) -> dict:
        res = self.graphQL_request(
            self._detailed_list_wf_query, {"workflowIds": [workflow_id]}
        )["workflows"]["workflows"][0]
        return {
            "model_groups": res["reviewableModelGroups"],
            "dataset_id": res["datasetId"],
            "workflow_name": res["name"],
            "workflow_id": res["id"],
        }

    def dataset_id(self, dataset_id: int) -> dict:
        query = """
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
        res = self.graphQL_request(query, {"id": dataset_id})["dataset"]
        wf_list = self.indico_client.call(ListWorkflows(dataset_ids=[dataset_id]))
        return {
            "workflow_ids": [wf.id for wf in wf_list],
            "model_groups": res["modelGroups"],
            "dataset_name": res["name"],
            "dataset_id": dataset_id,
        }

    def model_id(self, model_group_id: int) -> dict:
        query = """
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
        res = self.graphQL_request(query, {"id": model_group_id})["modelGroups"]["modelGroups"]
        dataset_workflows = self._workflows_from_dataset_id(res[0]["datasetId"])
        return {
            "model_group_name": res[0]["name"],
            "model_group_id": model_group_id,
            "selected_model_id": res[0]["selectedModel"]["id"],
            "dataset_id": res[0]["datasetId"],
            "workflow_ids": [
                wf["id"]
                for wf in dataset_workflows
                for model in wf["reviewableModelGroups"]
                if model["id"] == model_group_id
            ],
        }

    def _workflows_from_dataset_id(self, dataset_id: int):
        res = self.graphQL_request(
            self._detailed_list_wf_query, {"dataset_ids": [dataset_id]}
        )
        return res["workflows"]["workflows"]
