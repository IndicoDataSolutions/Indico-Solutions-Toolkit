from typing import List
from indico import IndicoClient
from .indico_wrapper import IndicoWrapper


class FindRelated(IndicoWrapper):
    def __init__(self, client: IndicoClient):
        self.client = client

    def questionnaire_id(self, questionnaire_id: int) -> dict:
        query = """
            query getCrowdlabelQuestionnaire($id: Int!) {
                    questionnaires(questionnaireIds: [$id]) {
                        questionnaires {
                            name
                            questions {
                                modelGroupId
                            }
                        }
                    }
                }
        """
        res = self.graphQL_request(query, {"id": questionnaire_id})["questionnaires"][
            "questionnaires"
        ][0]
        model_group_res = self.model_group_id(res["questions"][0]["modelGroupId"])
        return model_group_res

    def workflow_id(self, workflow_id: int) -> dict:
        """
        Given a workflow ID returns dictionary obj formatted like:
            {
                'model_groups': [
                    {
                        'id': 107,'name': 'My Extraction Model','selectedModel': {'id': 649}}
                        ],
                'dataset_id': 122,
                'workflow_name': 'Financial Loans 6/2_Bank Notices Extraction',
                'workflow_id': 141
            }
        """
        res = self._get_workflow_data(workflow_id=workflow_id)[0]
        questionnaires = []
        for model_group in res["reviewableModelGroups"]:
            q = self._get_questionnaire_by_model_group(model_group["id"])
            questionnaires.append(q["id"])
        return {
            "model_groups": res["reviewableModelGroups"],
            "dataset_id": res["datasetId"],
            "workflow_name": res["name"],
            "workflow_id": res["id"],
            "questionnaire_ids": questionnaires,
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
        wf_list = self._get_workflow_data(dataset_id=dataset_id)
        questionnaires = self._get_questionnaires_by_dataset_id(dataset_id)
        return {
            "workflow_ids": [wf["id"] for wf in wf_list],
            "model_groups": res["modelGroups"],
            "dataset_name": res["name"],
            "dataset_id": dataset_id,
            "questionnaire_ids": [q["id"] for q in questionnaires],
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
        workflow_response = self._get_workflow_data(dataset_id=res[0]["datasetId"])
        workflow_id = self._match_workflow_and_model_group(
            workflow_response, model_group_id
        )
        questionnaire = self._get_questionnaire_by_model_group(model_group_id)
        return {
            "model_group_name": res[0]["name"],
            "model_group_id": model_group_id,
            "selected_model_id": res[0]["selectedModel"]["id"],
            "dataset_id": res[0]["datasetId"],
            "workflow_id": workflow_id["id"],
            "questionnaire_id": questionnaire["id"],
            "questionnaire_name": questionnaire["name"],
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
        relevant_group = self._match_model_group_and_model_id(model_groups, model_id)
        workflow_data = self._get_workflow_data(
            dataset_id=[relevant_group["datasetId"]]
        )
        workflow_id = self._match_workflow_and_model_group(
            workflow_data, relevant_group["id"]
        )
        questionnaire = self._get_questionnaire_by_model_group(relevant_group["id"])
        return {
            "model_id": model_id,
            "model_group_id": relevant_group["id"],
            "model_name": relevant_group["name"],
            "dataset_id": relevant_group["datasetId"],
            "selected_model_id": relevant_group["selectedModel"]["id"],
            "workflow_id": workflow_id["id"],
            "questionnaire_id": questionnaire["id"],
            "questionnaire_name": questionnaire["name"],
        }

    def _get_workflow_data(
        self, dataset_id: int = None, workflow_id: int = None
    ) -> List[dict]:
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

    def _get_questionnaire_by_model_group(self, model_group_id: int) -> dict:
        questionnaires = self._get_all_questionnaires()
        for q in questionnaires:
            group_id = q["questions"][0]["modelGroupId"]
            if group_id == model_group_id:
                return q
        return {"id": None, "name": None}

    def _get_questionnaires_by_dataset_id(self, dataset_id: int) -> List[dict]:
        questionnaires = self._get_all_questionnaires()
        matching_qs = []
        for q in questionnaires:
            data_id = q["datasetId"]
            if data_id == dataset_id:
                matching_qs.append(q)
        return matching_qs

    def _get_all_questionnaires(self) -> List[dict]:
        query = """
            query getCrowdlabelQuestionnaires {
                questionnaires {
                    questionnaires {
                        id
                        name
                        datasetId
                        questions {
                            modelGroupId
                        }
                    }
                }
            }
        """
        return self.graphQL_request(query)["questionnaires"]["questionnaires"]

    @staticmethod
    def _match_workflow_and_model_group(
        workflow_response: List[dict], model_group: int
    ) -> dict:
        for workflow in workflow_response:
            for group in workflow["reviewableModelGroups"]:
                if group["id"] == model_group:
                    return workflow
        raise Exception(
            f"Model Group {model_group} doesn't exist in {workflow_response}"
        )

    @staticmethod
    def _match_model_group_and_model_id(
        model_response: List[dict], model_id: int
    ) -> dict:
        for group in model_response:
            for model in group["models"]:
                if model["id"] == model_id:
                    return group
        raise Exception(
            f"Model ID {model_id} doesn't exist or you don't have access to it"
        )
