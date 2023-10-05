from typing import List, Callable

class AutoReviewFunction:
    def __init__(
        self,
        function: Callable,
        labels: list = [],
        kwargs: dict = {},
    ):
        self.function = function
        self.labels = labels
        self.kwargs = kwargs

    def apply(self, predictions: List[dict] = []):
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
    ):
        self.predictions = predictions
        self.updated_predictions = predictions
        self.functions = []

    def apply_reviews(self) -> list:
        for function in self.functions:
            self.updated_predictions = function.apply(self.updated_predictions)
        return self.updated_predictions
    

