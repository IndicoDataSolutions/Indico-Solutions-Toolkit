import pytest
import os

from indico_toolkit.indico_wrapper import Teach
from tests.conftest import FILE_PATH


@pytest.fixture(scope="function")
def teach(indico_client, dataset_obj):
    return Teach(indico_client, dataset_obj.id)


@pytest.fixture(scope="function")
def teach_with_task(teach):
    teach.create_teach_task("Task Name", ["Class 1", "Class 2"], "Questions")
    return teach


def test_create_teach_task(teach):
    teach.create_teach_task("Task Name", ["Class 1", "Class 2"], "Questions")
    assert isinstance(teach.task_id, int)
    teach_task = teach.task
    assert teach_task.name == "Task Name"
    assert teach_task.labels == ["Class 1", "Class 2"]


def test_duplicate_teach_task(teach_with_task):
    old_id = teach_with_task.task.id
    teach_with_task.duplicate_teach_task(task_name="Duplicate")
    teach_task = teach_with_task.task
    assert teach_task.id != old_id
    assert teach_task.name == "Duplicate"
    assert teach_task.labels == ["Class 1", "Class 2"]


def test_label_with_snapshot(teach_with_task):
    status = teach_with_task.label_teach_task(
        os.path.join(FILE_PATH, "data/samples/fin_disc_snapshot.csv"),
        "question_1620",
        "row_index_6572",
    )
    assert status["submitLabels"]["success"] == True
    assert teach_with_task.task.num_fully_labeled == 51


def test_label(teach_with_task):
    status = teach_with_task.label_teach_task()
    assert status["submitLabels"]["success"] == True
    assert teach_with_task.task.num_fully_labeled == 77


def test_delete_teach_task(teach_with_task):
    status = teach_with_task.delete_teach_task()
    assert status["deleteQuestionnaire"]["success"] == True
