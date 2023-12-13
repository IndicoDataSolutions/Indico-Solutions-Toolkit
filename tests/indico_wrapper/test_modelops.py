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
        model_type="text_extraction",
        auto_negative_scaling=model_setting,
    )
    assert model_setting == new_setting["auto_negative_scaling"]


@pytest.mark.parametrize(
    "model_type",
    ["text_extractions", "text_classificatio", None],
)
def test_invalid_model_type(
    extraction_model_group_id, model_setting, modelop, model_type
):
    with pytest.raises(ValueError):
        _ = modelop.update_model_settings(
            model_group_id=extraction_model_group_id,
            model_type=model_type,
            auto_negative_scaling=model_setting,
        )


@pytest.mark.parametrize(
    "params",
    [
        ({"max_empty_chunk_ratio": -10}),
        ({"subtoken_prediction": True}),
        ({"base_models": "roberto"}),
    ],
)
def test_invalid_parameter(extraction_model_group_id, modelop, params):
    with pytest.raises(ValueError):
        _ = modelop.update_model_settings(
            model_group_id=extraction_model_group_id,
            model_type="text_extraction",
            **params
        )


def test_no_model_found(modelop, extraction_model_group_id):
    with pytest.raises(RuntimeError):
        _ = modelop.get_model_options(extraction_model_group_id, 00000)
