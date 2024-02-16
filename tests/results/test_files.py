from pathlib import Path

import pytest

from indico_toolkit import results

data_folder = Path(__file__).parent.parent / "data" / "results"


@pytest.mark.parametrize("result_file", list(data_folder.glob("v1*with_meta.json")))
def test_v1_with_reviews_meta_results(result_file: Path) -> None:
    result = results.load(result_file)
    assert result.submission_id
    assert not result.bundled
    assert result.models
    assert result.labels
    assert result.document.pre_review.classification.confidence
    assert result.document.pre_review.extractions[0].span.end


@pytest.mark.parametrize("result_file", list(data_folder.glob("v1*without_meta.json")))
def test_v1_without_reviews_meta_results(result_file: Path) -> None:
    with pytest.raises(results.ResultKeyError):
        results.load(result_file)


@pytest.mark.parametrize("result_file", list(data_folder.glob("v1*without_meta.json")))
def test_convert_v1_without_reviews_meta_results(result_file: Path) -> None:
    result = results.load(result_file, convert_unreviewed=True)
    assert result.submission_id
    assert not result.bundled
    assert result.models
    assert result.labels
    assert result.document.final.classification.confidence
    assert result.document.final.extractions[0].span.end


@pytest.mark.parametrize("result_file", list(data_folder.glob("v2*.json")))
def test_v2_results(result_file: Path) -> None:
    result = results.load(result_file)
    assert result.submission_id
    assert result.bundled
    assert result.models
    assert result.labels
    assert result.documents[0].pre_review.classification.confidence
    assert result.documents[0].pre_review.extractions[0].span.end


@pytest.mark.parametrize("result_file", list(data_folder.glob("v3*.json")))
def test_v3_results(result_file: Path) -> None:
    result = results.load(result_file)
    assert result.submission_id
    assert result.models
    assert result.labels
    assert result.documents[0].final.unbundlings[0].span.page == 0
    assert result.documents[0].final.extractions[0].span.end
