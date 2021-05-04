from typing import List


class WorkflowResult:
    def __init__(self, model_result: dict, model_name: str = None):
        self.result = model_result
        self.model_name = model_name

    def set_check_model_name(self):
        if self.model_name:
            self._check_is_valid_model_name()
        elif len(self.available_model_names) > 1:
            raise RuntimeError(
                f"Multiple models available, you must set self.model_name to one of {self.available_model_names}"
            )
        else:
            self.model_name = self.available_model_names[0]

    def _check_is_valid_model_name(self) -> None:
        if self.model_name not in self.available_model_names:
            raise KeyError(
                f"{self.model_name} is not an available model name. Options: {self.available_model_names}"
            )

    @property
    def pre_review_predictions(self) -> List[dict]:
        self.set_check_model_name()
        return self.document_results[self.model_name]["pre_review"]

    @property
    def post_review_predictions(self) -> List[dict]:
        self.set_check_model_name()
        return self.document_results[self.model_name]["final"]

    @property
    def predicitions(self) -> List[dict]:
        self.set_check_model_name()
        return self.document_results[self.model_name]

    @property
    def etl_url(self) -> str:
        return self.result["etl_url"]

    @property
    def document_results(self) -> dict:
        return self.result["results"]["document"]["results"]

    @property
    def available_model_names(self) -> list:
        return list(self.document_results.keys())
