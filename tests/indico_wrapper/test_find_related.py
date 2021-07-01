import pytest

from indico_toolkit.indico_wrapper import FindRelated


@pytest.fixture(scope="module")
def dataset_related(indico_client, dataset_obj):
    finder = FindRelated(indico_client)
    dataset_related = finder.dataset_id(dataset_obj.id)
    return dataset_related


@pytest.fixture(scope="module")
def finder(indico_client):
    return FindRelated(indico_client)


def test_questionnaire_id(finder, dataset_related):
    q_related = finder.questionnaire_id(dataset_related["questionnaire_ids"][0])
    assert q_related["dataset_id"] == dataset_related["dataset_id"]
    assert isinstance(q_related["workflow_id"], int) 


def test_workflow_id(workflow_id, finder, dataset_obj):
    related = finder.workflow_id(workflow_id)
    assert len(related["model_groups"]) == 1
    assert related["dataset_id"] == dataset_obj.id


def test_dataset_id(finder, dataset_obj):
    dataset_related = finder.dataset_id(dataset_obj.id)
    assert isinstance(dataset_related["workflow_ids"][0], int)
    assert isinstance(dataset_related["questionnaire_ids"][0], int)
    assert isinstance(dataset_related["model_groups"][0]["selectedModel"]["id"], int)


def test_model_group_id(finder, dataset_related):
    model_related = finder.model_group_id(dataset_related["model_groups"][0]["id"])
    assert isinstance(model_related["workflow_id"], int)
    assert model_related["dataset_id"] == dataset_related["dataset_id"]


def test_model_id(finder, dataset_related):
    model_id = dataset_related["model_groups"][0]["selectedModel"]["id"]
    model_group_id = dataset_related["model_groups"][0]["id"]
    model_data = finder.model_id(model_id)
    assert model_data["model_id"] == model_id
    assert model_data["dataset_id"] == dataset_related["dataset_id"]
    assert model_data["model_group_id"] == model_group_id
    assert isinstance(model_data["workflow_id"], int)
