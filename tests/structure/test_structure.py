import pytest
from indico_toolkit.structure import Structure
from indico.types import Workflow

@pytest.fixture(scope="module")
def test_structure(indico_client):
    test_structure = Structure(indico_client, path_to_file="")
    return test_structure

def test_structure_create_dataset(test_structure):
    pass

def test_create_workflow(test_structure):
    # test_wflow = test_structure.create_workflow(name="Test Workflow")
    # assert type(test_wflow) == Workflow
    # assert test_structure.workflow_id == test_structure.workflow.id
    pass

def test_create_workflow_exception_no_dataset(indico_client):
    empty_structure = Structure(indico_client, path_to_file="")
    with pytest.raises(Exception):
        empty_structure.create_workflow(name="Test Workflow")