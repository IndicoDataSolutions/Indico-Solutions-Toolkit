from indico.queries import ListWorkflows
from indico import IndicoClient
from solutions_toolkit.indico_wrapper import IndicoWrapper


class FindRelated(IndicoWrapper):
    def __init__(self, client: IndicoClient):
        self.client = client

    def workflow_id(self, workflow_id: int) -> dict:
        res = self._get_workflow_data(workflow_id=workflow_id)[0]
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
        wf_list = self.client.call(ListWorkflows(dataset_ids=[dataset_id]))
        return {
            "workflow_ids": [wf.id for wf in wf_list],
            "model_groups": res["modelGroups"],
            "dataset_name": res["name"],
            "dataset_id": dataset_id,
        }

    def model_group_id(self, model_group_id: int) -> dict:
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
        res = self.graphQL_request(query, {"id": model_group_id})["modelGroups"][
            "modelGroups"
        ]
        dataset_workflows = self._get_workflow_data(dataset_id=res[0]["datasetId"])
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

    def model_id(self, model_id: int):
        query = """
            {modelGroups {
                modelGroups {
                datasetId
                selectedModel{
                    id
                  }
                id
                name
                models{
                    id
                  }
                }
              }
            }
        """
        model_groups = self.graphQL_request(query)["modelGroups"]["modelGroups"]
        relevant_group = None
        for group in model_groups:
            for model in group["models"]:
                if model["id"] == model_id:
                    relevant_group = group
                    break
        if not relevant_group:
            raise Exception(f"ID {model_id} doesn't exist or you don't have access to it")
        workflow_data = self._get_workflow_data(dataset_id=[relevant_group["datasetId"]])
        workflow_id = None
        for flow in workflow_data:
            for group in flow["reviewableModelGroups"]:
                if group["id"] == relevant_group["id"]:
                    workflow_id = flow["id"]
                    break
        workflow_id = [i["id"] for i in workflow_data if i["reviewableModelGroups"]]
        return {
            "model_id": model_id,
            "model_group_id": relevant_group["id"],
            "model_name": relevant_group["name"],
            "dataset_id": relevant_group["datasetId"],
            "selected_model_id": relevant_group["selectedModel"]["id"],
            "workflow_id": workflow_id
        }


    def _get_workflow_data(self, dataset_id: int = None, workflow_id: int = None):
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
        assert dataset_id or workflow_id, "Must provide workflow or dataset ID"
        if dataset_id:
            variables = {"dataset_ids": [dataset_id]}
        else:
            variables = {"workflowIds": [workflow_id]}
        res = self.graphQL_request(query, variables)
        return res["workflows"]["workflows"]
