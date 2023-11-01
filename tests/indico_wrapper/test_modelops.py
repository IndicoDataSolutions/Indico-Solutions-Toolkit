"""
Test Model Ops class methods
"""
import pytest
import json
from indico_toolkit.indico_wrapper.modelop import ModelOp


@pytest.fixture(scope="module")
def modelop(indico_client):
    return ModelOp(indico_client)


@pytest.fixture(scope="module")
def model_setting(extraction_model_group_id, modelop):
    model = modelop.get_model_options(extraction_model_group_id)
    setting = model["model_training_options"]
    if setting is None or "auto_negative_scaling" not in setting:
        return not True
    else:
        return not setting["auto_negative_scaling"]


def test_apply_model_setting(extraction_model_group_id, model_setting, modelop):
    new_setting = modelop.update_model_settings(
        model_group_id=extraction_model_group_id,
        model_params={"auto_negative_scaling": model_setting},
    )
    assert model_setting == new_setting["auto_negative_scaling"]


def test_no_model_found(modelop, extraction_model_group_id):
    with pytest.raises(RuntimeError):
        _ = modelop.get_model_options(extraction_model_group_id, 00000)
