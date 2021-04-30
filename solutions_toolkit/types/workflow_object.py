from typing import List


class WorkflowResult:
    def __init__(self, model_result: dict, model_name: str = None):
        self.result = model_result
        self.model_name = self.set_model_name(model_name)

    def set_model_name(self, model_name):
        if model_name:
            self._check_is_valid_model_name()
        elif len(self.available_model_names) > 1:
            raise RuntimeError(
                f"Multiple models available, you must set self.model_name to one of {self.available_model_names}"
            )
        else:
            model_name = self.available_model_names[0]
        return model_name

    def _check_is_valid_model_name(self) -> None:
        if self.model_name not in self.available_model_names:
            raise KeyError(
                f"{self.model_name} is not an available model name. Options: {self.available_model_names}"
            )
    
    @property
    def pre_review_predictions(self) -> List[dict]:
        return self.result["results"]["document"]["results"][self.model_name][
            "pre_review"
        ]

    @property
    def post_review_predictions(self) -> List[dict]:
        return self.result["results"]["document"]["results"][self.model_name][
            "post_review"
        ]
    
    @property
    def predicitions(self) -> List[dict]:
        return self.result["results"]["document"]["results"][self.model_name]

    @property
    def etl_url(self) -> str:
        return self.result["etl_url"]

    @property
    def document_results(self) -> dict:
        return self.result["results"]["document"]["results"]
    
    @property
    def available_model_names(self) -> list:
        return list(self.document_results.keys())
    

