from pathlib import Path

import pytest

from indico_toolkit import results

data_folder = Path(__file__).parent.parent / "data" / "results"


@pytest.mark.parametrize("result_file", list(data_folder.glob("v1_reviewed*.json")))
def test_v1_reviewed_results(result_file: Path) -> None:
    submission = results.load(result_file)
    assert submission.id
    assert not submission.bundled
    assert submission.models
    assert submission.labels
    assert submission.document.pre_review.classification.confidence
    assert submission.document.pre_review.extractions[0].span.start


@pytest.mark.parametrize("result_file", list(data_folder.glob("v1_unreviewed*.json")))
def test_v1_unreviewed_results(result_file: Path) -> None:
    with pytest.raises(results.ResultFileError):
        results.load(result_file)


@pytest.mark.parametrize("result_file", list(data_folder.glob("v1_unreviewed*.json")))
def test_v1_converted_results(result_file: Path) -> None:
    submission = results.load(result_file, convert_unreviewed=True)
    assert submission.id
    assert not submission.bundled
    assert submission.models
    assert submission.labels
    assert submission.document.final.classification.confidence
    assert submission.document.final.extractions[0].span.start


@pytest.mark.parametrize("result_file", list(data_folder.glob("v2_unreviewed*.json")))
def test_v2_unreviewed_results(result_file: Path) -> None:
    submission = results.load(result_file)
    assert submission.id
    assert submission.bundled
    assert submission.models
    assert submission.labels
    assert submission.documents[0].pre_review.classification.confidence
    assert submission.documents[0].pre_review.extractions[0].span.start


@pytest.mark.parametrize("result_file", list(data_folder.glob("v3_unreviewed*.json")))
def test_v3_unreviewed_results(result_file: Path) -> None:
    submission = results.load(result_file)
    assert submission.id
    assert not submission.bundled
    assert submission.models
    assert submission.labels
    assert submission.document.final.unbundlings[0].span.page == 0
    assert submission.document.final.extractions[0].span.start
