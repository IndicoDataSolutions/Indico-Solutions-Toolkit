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

    def get_model_options(
        self, model_group_id: int, model_id: int | None = None
    ) -> dict[str, object]:
        """
        Return model options for `model_id` of `model_group_id`
        or the most recent model if `model_id` is not specified.
        Args:
            model_group_id (int): id of model group
            model_id (int, optional): argument to return a specific model within a model group
        """
        all_model_options = self.get_all_model_options(model_group_id)

        if model_id is None:
            return next(all_model_options)

        else:
            for model_options in all_model_options:
                if model_options["id"] == model_id:
                    return model_options
            else:
                raise RuntimeError(
                    f"Model group {model_group_id} does not have a model with ID {model_id}"
                )

    def get_all_model_options(self, model_group_id: int) -> Iterator[dict[str, object]]:
        """
        Return model options for all models of `model_group_id`.
        Args:
            model_group_id (int): id of model group
        Returns:
            dict: dictionary of all model options, including:
            "id", "domain, ""high_quality", "interlabeler_resolution",
            "sampling_strategy", "seed", "test_split", "weight_by_class_frequency",
            "word_predictor_strength", and "model_training_options"
        """

        response = self.client.call(
            GraphQLRequest(
                """
                query getMoonbowModelGroupModels($modelGroupId: Int!) {
                    modelGroup(modelGroupId: $modelGroupId) {
                        id
                        models {
                            id
                            modelOptions
                        }
                    }
                }
                """,
                {"modelGroupId": model_group_id},
            )
        )

        for model in response["modelGroup"]["models"]:
            model_options = json.loads(model["modelOptions"])
            model_options["id"] = model["id"]
            yield model_options

    def retrain_model(self, model_group_id: int) -> dict:
        """
        Forces model retrain.
        Args:
            model_group_id (int): id of model group needing retraining
        Returns:
            dict: returns model group id and status of retraining model
        """
        return self.client.call(
            GraphQLRequest(
                """
                mutation retrainMoonbowModelGroup($modelGroupId: Int!) {
                    retrainModelGroup(modelGroupId: $modelGroupId, forceRetrain: true) {
                        id
                        status
                    }
                }    
                """,
                {"modelGroupId": model_group_id},
            )
        )

    def update_model_settings(
        self, model_group_id: int, model_params: dict
    ) -> dict[str, object]:
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
            dict: Dictionary of advanced model training options
        """

        model = self.client.call(
            GraphQLRequest(
                """
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
                """,
                {
                    "modelGroupId": model_group_id,
                    "modelTrainingOptions": json.dumps(model_params),
                },
            )
        )
        options = json.loads(
            model["updateModelGroupSettings"]["modelOptions"]["modelTrainingOptions"]
        )
options["id"] = model["updateModelGroupSettings"]["modelOptions"]["id"]
        return options
