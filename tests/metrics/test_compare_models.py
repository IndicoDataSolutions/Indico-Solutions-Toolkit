import pytest
import tempfile
import pandas as pd

from indico_toolkit.metrics import CompareModels


def test_get_data_df(extraction_model_group_id, extraction_model_id, indico_client):
    comp = CompareModels(
        indico_client,
        extraction_model_group_id,
        extraction_model_id,
        extraction_model_group_id,
        extraction_model_id,
    )
    comp.get_data()
    assert isinstance(comp.df, pd.DataFrame)
    assert comp.df.shape[0] > 0
    assert len(comp.non_overlapping_fields) == 0


@pytest.fixture(scope="module")
def compare_obj(indico_client):
    model_1 = pd.DataFrame()
    model_1["precision_1"] = [0.5, 0.5, 0.5]
    model_1["f1Score_1"] = [0.5, 0.5, 0.5]
    model_1["field_name"] = ["a", "b", "c"]
    model_2 = pd.DataFrame()
    model_2["precision_2"] = [1, 1, 1]
    model_2["f1Score_2"] = [1, 1, 1]
    model_2["field_name"] = ["a", "b", "c"]
    comp = CompareModels(indico_client, 1, 1, 1, 2)
    comp.df = pd.merge(model_1, model_2, on="field_name")
    comp.overlapping_fields = set(["a", "b", "c"])
    return comp


def test_get_metric_differences(compare_obj):
    df = compare_obj.get_metric_differences()
    assert df.shape[1] == 4
    assert set(df.columns) == set(
        ["f1Score_1", "f1Score_2", "field_name", "difference"]
    )
    for val in df["difference"]:
        assert val == 0.5
