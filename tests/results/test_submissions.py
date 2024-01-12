import pytest
from pytest_mock import MockerFixture

from indico_toolkit.results import Document, ResultFileError, Submission


def test_result_file_version() -> None:
    with pytest.raises(ResultFileError):
        Submission.from_result(
            {
                "file_version": 0,
            },
        )


def test_reviews(mocker: MockerFixture) -> None:
    mocker.patch.object(Document, "_from_v1_result")

    submission = Submission.from_result(
        {
            "file_version": 1,
            "submission_id": 11,
            "etl_output": "indico-file:///etl_output.json",
            "results": {},
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

    assert submission.id == 11
    assert submission.version == 1
    assert submission.document == Document._from_v1_result.return_value
    assert len(submission.reviews) == 1
    assert submission.reviews[0].id == 2
    assert submission.rejected is False


def test_null_review(mocker: MockerFixture) -> None:
    mocker.patch.object(Document, "_from_v1_result")

    submission = Submission.from_result(
        {
            "file_version": 1,
            "submission_id": 10,
            "etl_output": "indico-file:///etl_output.json",
            "reviews_meta": [{"review_id": None}],
        },
    )

    assert not submission.reviews


def test_missing_reviews() -> None:
    with pytest.raises(ResultFileError):
        Submission.from_result(
            {
                "file_version": 1,
                "results": {},
            },
        )
