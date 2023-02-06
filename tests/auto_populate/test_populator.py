import pytest
import tempfile
import os
import pandas as pd
from indico_toolkit.auto_populate import AutoPopulator

def test_create_classifier_too_few_classes(indico_client, testdir_file_path):
    auto_populator = AutoPopulator(
        indico_client, os.path.join(testdir_file_path, "data/auto_class")
    )
    auto_populator.set_file_paths()
    auto_populator.create_populator("My dataset", "My workflow", "My teach task", "my_labelset")
