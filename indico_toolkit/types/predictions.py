from typing import List, Dict, Set

from indico_toolkit.errors import ToolkitInputError
from .extractions import Extractions
from .classification import Classification, ClassificationMGP

class Predictions:
    """
    Factory class for predictions
    """
    @staticmethod
    def get_obj(predictions):
        """
        Returns:
        Extractions object or Classification object depending on predictions type
        """
        if type(predictions) == list:
            return Extractions(predictions)
        elif type(predictions) == dict:
            if "label" in predictions:
                return Classification(predictions)
            else:
                return ClassificationMGP(predictions)
        else:
            raise ToolkitInputError(f"Unable to process predictions with type {type(predictions)}. Predictions: {predictions}")
