from typing import List


class ExtractionResult:
    def __init__(self, model_result: dict, model_name: str = None):
        self.result = model_result
        self.model_name = model_name

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
    def models(self) -> list:
        return list(self.document_results.keys())
    
    # How to handle multiple model names
        # Instantiate new object for each model
    # How to handle multiple types of outputs (extraction vs classification)
        # Separate classes?

