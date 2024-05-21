from pathlib import Path

import pytest

from indico_toolkit import results

data_folder = Path(__file__).parent.parent / "data" / "results"


@pytest.mark.parametrize("result_file", list(data_folder.glob("*.json")))
def test_file_load(result_file: Path) -> None:
    result = results.load(result_file)
    result.pre_review.to_changes(result)
    assert result.version
