from typing import List, Dict, Set

import indico_toolkit.types
from indico_toolkit.errors import ToolkitInputError


class Predictions:
    """
    Factory class for predictions
    """
    @staticmethod
    def get_obj(predictions):
        """
        Returns:
        Extractions object or Classifications object depending on predictions type
        """
        if type(predictions) == list:
            return indico_toolkit.types.Extractions(predictions)
        elif type(predictions) == dict:
            return indico_toolkit.types.Classifications(predictions)
        else:
            raise ToolkitInputError(f"Unable to process predictions with type {type(predictions)}")
