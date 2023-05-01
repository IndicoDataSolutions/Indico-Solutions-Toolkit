from enum import Enum

class ModelTaskType(Enum):
    """Issues with SDK 7/15/22-- need to hard code this here, new SDK release with fix is imminent"""

    CLASSIFICATION = 1
    FORM_EXTRACTION = 2
    OBJECT_DETECTION = 3
    CLASSIFICATION_MULTIPLE = 4
    REGRESSION = 5
    ANNOTATION = 6
    CLASSIFICATION_UNBUNDLING = 7