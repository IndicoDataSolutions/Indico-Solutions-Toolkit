import os
import pytest
import time
from indico.queries import GetWorkflow
from indico.types import Workflow
from indico_toolkit.auto_populate import AutoPopulator


def test_create_classification_workflow(indico_client, testdir_file_path):
    auto_populator = AutoPopulator(indico_client)
    auto_populator.set_file_paths(os.path.join(testdir_file_path, "data/auto_class"))
    assert len(auto_populator.file_paths) == 2
    new_workflow = auto_populator.create_auto_classification_workflow(
        "My dataset", "My workflow", "My teach task", "my_labelset"
    )
    assert isinstance(new_workflow, Workflow)


def test_create_classification_workflow_too_few_classes(
    indico_client, testdir_file_path
):
    auto_populator = AutoPopulator(indico_client)
    auto_populator.set_file_paths(os.path.join(testdir_file_path, "data/auto_class/class_a/"))
    with pytest.raises(Exception):
        auto_populator.create_auto_classification_workflow(
            "My dataset", "My workflow", "My teach task", "my_labelset"
        )


def test_copy_workflow(indico_client, dataset_obj, workflow_id):
    auto_populator = AutoPopulator(indico_client)
    original_workflow = indico_client.call(GetWorkflow(workflow_id))
    print(original_workflow.id)
    new_workflow = auto_populator.copy_workflow(
        dataset_id=dataset_obj.id,
        teach_task_id=original_workflow.components[-1].model_group.questionnaire_id,
        workflow_name=f"{original_workflow.name}_Copied",
        data_column="text"
    )
    assert isinstance(new_workflow, Workflow)
