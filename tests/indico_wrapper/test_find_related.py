from solutions_toolkit.indico_wrapper import FindRelated

def test_workflow_id(workflow_id, indico_client, dataset_obj):
    finder = FindRelated(indico_client)
    related = finder.workflow_id(workflow_id)
    assert len(related["model_groups"]) == 1
    assert related["dataset_id"] == dataset_obj.id

def test_dataset_and_model_group_id(indico_client, dataset_obj):
    finder = FindRelated(indico_client)
    dataset_related = finder.dataset_id(dataset_obj.id)
    assert isinstance(dataset_related["workflow_ids"][0], int)
    assert isinstance(dataset_related["model_groups"][0]["selectedModel"]["id"], int)
    model_related = finder.model_id(dataset_related["model_groups"][0]["id"])
    assert isinstance(model_related["workflow_ids"][0], int)
