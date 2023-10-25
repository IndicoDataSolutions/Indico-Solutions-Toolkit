from indico import IndicoClient
from indico.queries import GraphQLRequest
import json
import string


class ModelOp:

    """
    Class to assit in Model Group Operation calls.
    """

    def __init__(self, client: IndicoClient):
        self.client = client
        self.task_type = None

    def get_model_group(self, model_group_id: int) -> dict: 
        """
        Get specified model group information.
        Args:
            model_group_id (int): id of model group 
        Returns:
            dict: attributes of the specified model group id 
        """

        query = """
        
query GetModelGroup($id: Int) {
  modelGroups(modelGroupIds: [$id]) {
    modelGroups {
      id
      name
      status
      taskType
      selectedModel {
        id
        status
      }
      modelOptions {
        id
        samplingStrategy
        modelTrainingOptions
      }
    }
  }
}
                """
        
        results = self.client.call(
            GraphQLRequest(query, {"modelGroupId": model_group_id})
        )
        models = results["modelGroups"]["modelGroups"]
        for model in models:
            if model["id"] == model_group_id:
                #assign task type for advanced model options
                self.task_type = model["taskType"]
                #assign model settings for validation
                self.model_setings = json.loads(model["modelOptions"]["modelTrainingOptions"])
                return model

    def retrain_model(self, model_group_id: int):
        """
        Forces model retrain, used within update_model_settings to apply new Training Options.
        Args:
            model_group_id (int): id of model group needing retraining
        """

        query = """

mutation retrainMoonbowModelGroup($modelGroupId: Int!) {
  retrainModelGroup(modelGroupId: $modelGroupId, forceRetrain: true) {
    id
    status
    __typename
  }
}    
                """
        
        self.client.call(GraphQLRequest(query, {"modelGroupId": model_group_id}))
        return

    def list_models(self, model_group_id: int) -> list[dict]:
        """
        Returns all avaible models within a model group. Used to show new model ID after retraining. 
        Args:
            model_group_id (int): id of model group 
        Returns:
            list[dict]: List of dictionaries for each model and its corresponding attributes
        """

        query = """

query getMoonbowModelGroupModels($modelGroupId: Int!) {
  modelGroup(modelGroupId: $modelGroupId) {
    id
    models {
      id
      modelOptions
    }
  }
}
                """
        
        results = self.client.call(
            GraphQLRequest(query, {"modelGroupId": model_group_id})
        )
        models = results["modelGroup"]["models"]
        self.latest_model = models[0]
        return models

    def update_model_settings(self, model_group_id: int, model_parms: dict, retrain : bool =False) -> dict:
        """
        Update model settings based on model type and specified model training options.

        Args:
             model_group_id (int): id of model group 
             model_parms (dict): JSONString of Advanced Model Training Options

                    Text Extraction
                        max_empty_chunk_ratio : 1.0
                        auto_negative_scaling : True
                        optimize_for : "predict_speed" ( "predict_speed", "accuracy", "speed", "accuracy_fp16" and "predict_speed_fp16")
                        subtoken_prediction : True
                        base_model : "roberta" ("roberta", "small" (distilled version of RoBERTa), "multilingual", "fast", "textcnn", "fasttextcnn")
                        class_weight : "sqrt" ("linear", "sqrt", "log", None)

                    Text Classification
                        model_type : "standard" (“tfidf_lr”, “tfidf_gbt”, “standard”, “finetune”)

                    Object Detection / Image Classification
                        filter_empty : False
                        n_epochs : (unspecified)
                        use_small_model : False

            retrain (bool) : Declare whether model should be retrained after updating advanced model settings.
        Returns:
            dict: Dictionary showing all model training options
        """

        query = """

mutation updateModelGroup($modelGroupId: Int!, $modelTrainingOptions: JSONString) {
  updateModelGroupSettings(
    modelGroupId: $modelGroupId
    modelTrainingOptions: $modelTrainingOptions
  ) {
    modelOptions {
      id
      modelTrainingOptions
    }
  }
}

                """
        # add model type logic
        model = self.client.call(
            GraphQLRequest(
                query,
                {
                    "modelGroupId": model_group_id,
                    "modelTrainingOptions": json.dumps(model_parms),
                },
            )
        )
        options = json.loads(model['updateModelGroupSettings']['modelOptions']['modelTrainingOptions'])

        if retrain:
            self.retrain_model(model_group_id)

            print(f'new model id {self.list_models(model_group_id)[0]["id"]}')
            return options
        return options

    def get_status(self, model_group_id: int, model_id: int) -> dict:
        """
        Get status of specified model id within a model group.
        Args:
            model_group_id (int): id of model group 
            model_id (int): id of model 
        Returns:
            list[dict]: Dictionary of model showing status and training progress
        """

        query = """

query getMoonbowModelTrainingStatus($modelGroupId: Int!, $modelId: Int!) {
  modelGroups(modelGroupIds: [$modelGroupId]) {
    modelGroups {
      model(id: $modelId) {
        id
        status
        trainingProgress {
          percentComplete
        }
      }
    }
  }
}

                """
        results = self.client.call(
            GraphQLRequest(query, {"modelGroupId": model_group_id, "modelId": model_id})
        )
        return results
