from indico import types

from solutions_toolkit.indico_wrapper import FindRelated


def test_workflow_id(workflow_id, find_related_wrapper, dataset):
    related = find_related_wrapper.workflow_id(workflow_id)
    assert len(related["model_groups"]) == 1
    assert related["dataset_id"] == dataset.id


def test_dataset_and_model_group_id(dataset, find_related_wrapper):
    dataset_related = find_related_wrapper.dataset_id(dataset.id)
    assert isinstance(dataset_related["workflow_objects"][0], types.Workflow)
    assert isinstance(dataset_related["model_groups"][0]["selectedModel"]["id"], int)
    model_related = find_related_wrapper.model_id(dataset_related["model_groups"][0]["id"])
    assert isinstance(model_related["workflows"][0], dict)
