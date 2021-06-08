import pytest
import os

from indico_toolkit.indico_wrapper import Teach
from tests.conftest import FILE_PATH


@pytest.fixture(scope="module")
def teach(indico_client, dataset_obj):
    return Teach(indico_client, dataset_obj.id)


def test_create_teach_task(teach):
    teach.create_teach_task("Task Name", ["Class 1", "Class 2"], "Questions")
    assert isinstance(teach.task_id, int)
    teach_task = teach.task
    assert teach_task.name == "Task Name"
    assert teach_task.labels == ["Class 1", "Class 2"]


def test_duplicate_teach_task(teach):
    old_id = teach.task.id
    teach.duplicate_teach_task(task_name="Duplicate")
    teach_task = teach.task
    assert teach_task.id != old_id
    assert teach_task.name == "Duplicate"
    assert teach_task.labels == ["Class 1", "Class 2"]


def test_label_with_snapshot(teach):
    status = teach.label_teach_task(
        os.path.join(FILE_PATH, "data/samples/fin_disc_snapshot.csv"),
        "question_1620",
        "row_index_6572",
    )
    assert status["submitLabels"]["success"] == True
    assert teach.task.num_fully_labeled == 51


def test_label(teach):
    status = teach.label_teach_task()
    assert status["submitLabels"]["success"] == True
    assert teach.task.num_fully_labeled == 102


def test_delete_teach_task(teach):
    status = teach.delete_teach_task()
    assert status["deleteQuestionnaire"]["success"] == True
