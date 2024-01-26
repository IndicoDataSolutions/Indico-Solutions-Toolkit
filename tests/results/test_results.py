import pytest
from pytest_mock import MockerFixture

from indico_toolkit.results import Document, Result, ResultKeyError


def test_result_file_version() -> None:
    with pytest.raises(ResultKeyError):
        Result.from_result(
            {
                "file_version": 0,
            },
        )


def test_reviews(mocker: MockerFixture) -> None:
    mocker.patch.object(Document, "_from_v1_result")

    result = Result.from_result(
        {
            "file_version": 1,
            "submission_id": 11,
            "reviews_meta": [
                {
                    "review_id": 2,
                    "reviewer_id": 7,
                    "review_notes": None,
                    "review_rejected": False,
                    "review_type": "manual",
                },
            ],
        },
    )

    assert result.submission_id == 11
    assert result.file_version == 1
    assert result.document == Document._from_v1_result.return_value
    assert len(result.reviews) == 1
    assert result.reviews[0].id == 2
    assert result.rejected is False


def test_null_review(mocker: MockerFixture) -> None:
    mocker.patch.object(Document, "_from_v1_result")

    result = Result.from_result(
        {
            "file_version": 1,
            "submission_id": 10,
            "reviews_meta": [
                {"review_id": None},
            ],
        },
    )

    assert not result.reviews


def test_missing_reviews() -> None:
    with pytest.raises(ResultKeyError):
        Result.from_result(
            {
                "file_version": 1,
                "results": {},
            },
        )
