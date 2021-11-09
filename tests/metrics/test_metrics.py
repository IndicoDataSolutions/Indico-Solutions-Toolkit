import pytest
import tempfile
import pandas as pd

from indico_toolkit.metrics import ExtractionMetrics


def test_get_metrics(extraction_model_group_id, indico_client):
    metrics = ExtractionMetrics(indico_client)
    metrics.get_metrics(extraction_model_group_id)
    assert isinstance(metrics.included_models, list)
    assert isinstance(metrics.included_models[0], int)
    assert isinstance(metrics.raw_metrics, list)
    assert isinstance(metrics.raw_metrics[0], dict)
    assert isinstance(metrics.number_of_samples, dict)
    assert isinstance(list(metrics.number_of_samples.values())[0], int)
    assert isinstance(list(metrics.number_of_samples.keys())[0], int)
    assert "id" in metrics.raw_metrics[0] and "evaluation" in metrics.raw_metrics[0]


@pytest.fixture(scope="module")
def ex_metrics_object(extraction_model_group_id, indico_client):
    metrics = ExtractionMetrics(indico_client)
    metrics.get_metrics(extraction_model_group_id)
    return metrics


def test_get_metrics_df(ex_metrics_object):
    df = ex_metrics_object.get_metrics_df()
    assert "precision" in df.columns and "f1Score" in df.columns
    assert isinstance(df["precision"][0], float)
    assert "field_name" in df.columns and "model_id" in df.columns
    assert isinstance(df["field_name"][0], str)
    assert "number_of_samples" in df.columns
    assert int(df["number_of_samples"][0])


def test_get_metrics_df_one_id(ex_metrics_object, extraction_model_id):
    df = ex_metrics_object.get_metrics_df(select_model_id=extraction_model_id)
    assert len(df["model_id"].unique()) == 1


def test_get_metrics_df_exact(ex_metrics_object):
    df = ex_metrics_object.get_metrics_df(span_type="exact")
    assert "precision" in df.columns and "f1Score" in df.columns
    assert isinstance(df["precision"][0], float)
    assert "field_name" in df.columns and "model_id" in df.columns
    assert isinstance(df["field_name"][0], str)


def test_to_csv(ex_metrics_object):
    with tempfile.NamedTemporaryFile(suffix=".csv") as tf:
        ex_metrics_object.to_csv(tf.name)
        df = pd.read_csv(tf.name)
        assert df.shape[0] > 0
        assert "field_name" in df.columns and "model_id" in df.columns
