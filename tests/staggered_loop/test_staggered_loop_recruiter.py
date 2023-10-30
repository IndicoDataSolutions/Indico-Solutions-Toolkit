import pytest
import json
import pandas as pd
from indico_toolkit.staggered_loop import StaggeredLoopRecruiter


@pytest.fixture(scope="function")
def static_reviewed_extract_results():
    with open("tests/data/samples/staggered_loop_recruiter_example.json") as infile:
        results = json.load(infile)
    return results


def test_get_field_performance(indico_client, static_reviewed_extract_results):
    recruiter = StaggeredLoopRecruiter(indico_client, "Toolkit Test Financial Model")
    df = recruiter.get_field_performance([static_reviewed_extract_results], "Asset Value")
    precision = df["Precision"]
    recall = df["Recall"]
    rejected_preds = df["Rejected Predictions"]
    added_preds = df["Added Predictions"]
    assert precision.item() == 1
    assert recall.item() == 1
    assert not rejected_preds.item()
    assert not added_preds.item()
