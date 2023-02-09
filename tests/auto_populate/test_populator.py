import os
import pytest
from indico_toolkit.auto_populate import AutoPopulator

def test_create_populator(indico_client, testdir_file_path):
    auto_populator = AutoPopulator(
        indico_client, os.path.join(testdir_file_path, "data/auto_class")
    )
    auto_populator.set_file_paths()
    assert len(auto_populator.file_paths) == 2
    auto_populator.create_populator("My dataset", "My workflow", "My teach task", "my_labelset")


def test_create_populator_too_few_classes(indico_client, testdir_file_path):
    auto_populator = AutoPopulator(
        indico_client, os.path.join(testdir_file_path, "data/auto_class/class_a")
    )
    auto_populator.set_file_paths()
    with pytest.raises(Exception):
        auto_populator.create_populator("My dataset", "My workflow", "My teach task", "my_labelset")