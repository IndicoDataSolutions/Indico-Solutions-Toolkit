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
        # self.task_type = None
        self.model_settings = None
        self.model_list = None

    def get_model_settings(self, model_group_id: int, model_id: int = None) -> dict:
        """
        Returns options of most recent model within a model group as a dictionary. If a specific model id is passed, that corresponding options dictionary is returned.
        model_list attribute contains all available models as a list. model_settings contains most recent model's training options
        Args:
            model_group_id (int): id of model group
            model_id (int, optional): argument to return a specific model within a model group
        Returns:
            dict: dictionary of all model options, including: 
            "id", "domain, ""high_quality", "interlabeler_resolution",
            "sampling_strategy", "seed", "test_split", "weight_by_class_frequency",
            "word_predictor_strength", and "model_training_options"

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
        self.model_list = models
        self.model_settings = json.loads(models[0]["modelOptions"])[
            "model_training_options"
        ]

        if not model_id:
            return models[0]
        else:
            for model in models:
                if model["id"] == model_id:
                    return model

    def retrain_model(self, model_group_id: int) -> dict:
        """
        Forces model retrain.
        Args:
            model_group_id (int): id of model group needing retraining
        Returns:
            dict: returns model group id and status of retraining model
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
        return self.client.call(GraphQLRequest(query, {"modelGroupId": model_group_id}))

    def update_model_settings(self, model_group_id: int, model_parms: dict) -> dict:
        """
        Update group model settings based on specified model training options.

        Args:
             model_group_id (int): id of model group
             model_parms (dict): Dictionary of Advanced Model Training Options

            Default values of Advanced Model Training Options and the avaiable parameters:
                    For Text Extraction Model:
                        max_empty_chunk_ratio : 1.0
                        auto_negative_scaling : True
                        optimize_for : "predict_speed" ( "predict_speed", "accuracy", "speed", "accuracy_fp16" and "predict_speed_fp16")
                        subtoken_prediction : True
                        base_model : "roberta" ("roberta", "small" (distilled version of RoBERTa), "multilingual", "fast", "textcnn", "fasttextcnn")
                        class_weight : "sqrt" ("linear", "sqrt", "log", None)

                    For Text Classification Model:
                        model_type : "standard" (“tfidf_lr”, “tfidf_gbt”, “standard”, “finetune”)
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
        options = json.loads(
            model["updateModelGroupSettings"]["modelOptions"]["modelTrainingOptions"]
        )

        return options
