import os

from indico_toolkit.indico_wrapper import Teach


def test_create_label_teach(indico_client, dataset_obj, testdir_file_path):
    teach = Teach(indico_client, dataset_obj.id)
    teach.create_teach_task("Task Name", ["Class 1", "Class 2"], "Questions")
    status = teach.label_teach_task(
        os.path.join(testdir_file_path, "data/samples/fin_disc_snapshot.csv"),
        "question_1620",
        "row_index_6572",
    )
    assert status["submitLabels"]["success"] == True
    assert teach.task.num_fully_labeled == 51
