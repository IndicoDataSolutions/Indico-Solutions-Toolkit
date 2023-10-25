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
    model = modelop.get_model_group(extraction_model_group_id)
    setting = json.loads(model["modelOptions"]["modelTrainingOptions"])
    if setting is None or "auto_negative_scaling" not in setting:
        updated_model = modelop.update_model_settings(
            extraction_model_group_id, model_parms={"auto_negative_scaling": True}
        )
        return updated_model["auto_negative_scaling"]
    else:
        return setting["auto_negative_scaling"]


def test_apply_model_setting(extraction_model_group_id, model_setting, modelop):
    new_model = modelop.update_model_settings(model_group_id = 
        extraction_model_group_id,
        model_parms={"auto_negative_scaling": not model_setting}
    )

    assert model_setting != new_model["auto_negative_scaling"]