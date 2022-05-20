import pytest
import tempfile
import pandas as pd
from indico.types.user_metrics import UserSnapshot
from indico_toolkit.metrics import UserMetrics

mock_snapshot = [
    UserSnapshot(
        id=1478011,
        name="John Doe",
        email="john.doe@email.com",
        enabled=True,
        created_at="2022-02-28T16:57:34",
        roles=["APP_ADMIN", "TEAM_DEVELOPER", "CELERY_FLOWER"],
        datasets=[],
    )
]


@pytest.fixture(scope="module")
def ex_user_metrics_object(indico_client):
    user_metrics = UserMetrics(indico_client, filter_user_id=1478011)
    return user_metrics


def test_get_dataframe(ex_user_metrics_object):
    ex_user_metrics_object.user_snapshots = [mock_snapshot]
    df = ex_user_metrics_object.get_metrics_df()

    assert df.shape[0] > 0
    assert "id" in df.columns and "name" in df.columns
    assert "email" in df.columns and "enabled" in df.columns
    assert "roles" in df.columns and "created_at" in df.columns
    assert "datasets" in df.columns


def test_to_csv(ex_user_metrics_object):
    with tempfile.NamedTemporaryFile(suffix=".csv") as tf:
        ex_user_metrics_object.get_metrics_df()
        ex_user_metrics_object.to_csv(tf.name)
        df = pd.read_csv(tf.file)

        assert df.shape[0] > 0
        assert "id" in df.columns and "name" in df.columns
        assert "email" in df.columns and "enabled" in df.columns
        assert "roles" in df.columns and "created_at" in df.columns
        assert "datasets" in df.columns
