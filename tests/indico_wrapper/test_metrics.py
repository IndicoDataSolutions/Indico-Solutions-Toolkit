import pytest
from indico_toolkit.indico_wrapper import ExtractionMetrics

def test_get_metrics(extraction_model_group_id, indico_client):
    metrics = ExtractionMetrics(indico_client)
    metrics.get_metrics(extraction_model_group_id)
    assert isinstance(metrics.included_models, list)
    assert isinstance(metrics.included_models[0], int)
    assert isinstance(metrics.raw_metrics, list)
    assert isinstance(metrics.raw_metrics[0], dict)
    assert "id" in metrics.raw_metrics[0] and "evaluation" in metrics.raw_metrics[0]
