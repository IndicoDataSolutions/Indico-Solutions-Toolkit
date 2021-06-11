from _pytest.python import Class
from tests.types.conftest import extractions_obj
import pytest

from indico_toolkit.types import Predictions, Extractions, Classifications
from indico_toolkit.errors import ToolkitInputError


def test_bad_type():
    with pytest.raises(ToolkitInputError):
        Predictions.get_obj("Bad type")


def test_get_obj_extractions(static_extract_preds):
    extraction_obj = Predictions.get_obj(static_extract_preds)
    assert type(extraction_obj) == Extractions
    assert extraction_obj._preds == static_extract_preds


def test_get_obj_classifications(static_class_preds):
    classification_obj = Predictions.get_obj(static_class_preds)
    assert type(classification_obj) == Classifications
    assert classification_obj._preds == static_class_preds
