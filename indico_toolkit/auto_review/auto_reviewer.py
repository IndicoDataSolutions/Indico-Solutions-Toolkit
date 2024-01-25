from typing import Dict, List, Callable

class AutoReviewFunction:
    """
    Class for hosting functions to manipulate predictions before sending to 
    auto review

    Args:
        function (Callable): method to be invoked when applying reviews. 
        The Callable must have the following arguments in the following order:
            predictions (List[dict]),
            labels (List[str]),
            **kwargs,

        labels (List[str]): list of labels to invoke method on. Defaults to all labels
        kwargs (Dict[str, str]): dictionary containing additional arguments needed in calling function
    """
    def __init__(
        self,
        function: Callable,
        labels: List[str] = [],
        kwargs: Dict[str, str] = {},
    ):
        self.function = function
        self.labels = labels
        self.kwargs = kwargs

    def apply(self, predictions: List[dict]):
        if predictions and not self.labels:
            self.labels = list(set([pred["label"] for pred in predictions]))
        return self.function(predictions, self.labels, **self.kwargs)



class AutoReviewer:
    """
    Class for programatically reviewing workflow predictions

    Example Usage:

    reviewer = AutoReviewer(
        predictions, functions
    )

    # Get your updated predictions
    updated_predictions: List[dict] = reviewer.apply_reviews()
    """

    def __init__(
        self,
        predictions: List[dict],
        functions: List[AutoReviewFunction] = []
    ):
        self.predictions = predictions
        self.updated_predictions = predictions
        self.functions = functions

    def apply_reviews(self) -> list:
        for function in self.functions:
            self.updated_predictions = function.apply(self.updated_predictions)
        return self.updated_predictions
    

