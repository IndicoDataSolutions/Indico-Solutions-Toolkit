from pathlib import Path

import pytest

from indico_toolkit import results

data_folder = Path(__file__).parent.parent / "data" / "results"


@pytest.mark.parametrize("result_file", list(data_folder.glob("v1_reviewed*.json")))
def test_v1_reviewed_results(result_file: Path) -> None:
    result = results.load(result_file)
    assert result.submission_id
    assert not result.bundled
    assert result.models
    assert result.labels
    assert result.document.pre_review.classification.confidence
    assert result.document.pre_review.extractions[0].span.start


@pytest.mark.parametrize("result_file", list(data_folder.glob("v1_unreviewed*.json")))
def test_v1_unreviewed_results(result_file: Path) -> None:
    with pytest.raises(results.ResultKeyError):
        results.load(result_file)


@pytest.mark.parametrize("result_file", list(data_folder.glob("v1_unreviewed*.json")))
def test_v1_converted_results(result_file: Path) -> None:
    result = results.load(result_file, convert_unreviewed=True)
    assert result.submission_id
    assert not result.bundled
    assert result.models
    assert result.labels
    assert result.document.final.classification.confidence
    assert result.document.final.extractions[0].span.start


@pytest.mark.parametrize("result_file", list(data_folder.glob("v2_unreviewed*.json")))
def test_v2_unreviewed_results(result_file: Path) -> None:
    result = results.load(result_file)
    assert result.submission_id
    assert result.bundled
    assert result.models
    assert result.labels
    assert result.documents[0].pre_review.classification.confidence
    assert result.documents[0].pre_review.extractions[0].span.start


@pytest.mark.parametrize("result_file", list(data_folder.glob("v3_unreviewed*.json")))
def test_v3_unreviewed_results(result_file: Path) -> None:
    result = results.load(result_file)
    assert result.submission_id
    assert not result.bundled
    assert result.models
    assert result.labels
    assert result.document.final.unbundlings[0].span.page == 0
    assert result.document.final.extractions[0].span.start
