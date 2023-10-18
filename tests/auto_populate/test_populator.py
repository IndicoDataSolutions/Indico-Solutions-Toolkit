import os
import pytest
import time
import json
import pandas as pd
from indico.queries import GetWorkflow
from indico.types import Workflow
from indico_toolkit.auto_populate.types import LabelInput, LabelInst
from indico_toolkit.auto_populate import AutoPopulator


@pytest.fixture(scope="function")
def static_file_to_targets(populator_snapshot_csv_path):
    df = pd.read_csv(populator_snapshot_csv_path)
    file_to_targets = {}
    for file, target in zip(df["file_name_1820"].to_list(), df["Toolkit Test Financial Model"].to_list()):
        if not isinstance(target, float):
            file_to_targets[file] = json.loads(target)["targets"]
    return file_to_targets


def test_create_classification_workflow(indico_client, testdir_file_path):
    auto_populator = AutoPopulator(indico_client)
    new_workflow = auto_populator.create_auto_classification_workflow(
        os.path.join(testdir_file_path, "data/auto_class"),
        "My dataset",
        "My workflow",
        "My teach task",
    )
    assert len(auto_populator._fp.file_paths) == 2
    assert isinstance(new_workflow, Workflow)


def test_create_classification_workflow_too_few_classes(
    indico_client, testdir_file_path
):
    auto_populator = AutoPopulator(indico_client)
    with pytest.raises(Exception):
        auto_populator.create_auto_classification_workflow(
            os.path.join(testdir_file_path, "data/auto_class/class_a/"),
            "My dataset",
            "My workflow",
            "My teach task",
        )


def test_copy_teach_task(indico_client, dataset_obj, workflow_id, teach_task_id):
    auto_populator = AutoPopulator(indico_client)
    original_workflow = indico_client.call(GetWorkflow(workflow_id))
    new_workflow = auto_populator.copy_teach_task(
        dataset_id=dataset_obj.id,
        teach_task_id=teach_task_id,
        workflow_name=f"{original_workflow.name}_Copied",
        data_column="text",
    )
    assert isinstance(new_workflow, Workflow)


def test_get_labels_by_filename(
    indico_client, extraction_model_group_id, teach_task_id, static_file_to_targets
):
    populator = AutoPopulator(indico_client)
    (
        labelset_id,
        model_group_id,
        target_name_map,
    ) = populator._get_teach_task_details(teach_task_id)

    labels = populator.get_labels_by_filename(
        extraction_model_group_id,
        static_file_to_targets,
        target_name_map
    )
    assert(len(labels) != 0)
    for label in labels:
        assert isinstance(label, LabelInput)
        for target in label.targets:
            assert isinstance(target, LabelInst)