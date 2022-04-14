import pytest
import tempfile
import pandas as pd
from typing import List

from indico_toolkit.metrics import UserMetrics

@pytest.fixture(scope="module")
def ex_user_metrics_object(indico_client):
    user_metrics = UserMetrics(indico_client)
    return user_metrics


def test_to_csv(ex_user_metrics_object):
    with tempfile.NamedTemporaryFile(suffix=".csv") as tf:
        ex_user_metrics_object.to_csv(tf.name)
        df = pd.read_csv(tf.file)
        assert df.shape[0] > 0
        assert "id" in df.columns and "name" in df.columns
        assert "email" in df.columns and "enabled" in df.columns
        assert "roles" in df.columns and "created_at" in df.columns
        assert list(df["datasets"][0])