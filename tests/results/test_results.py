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
    mock_from_v1_result = mocker.patch.object(Document, "_from_v1_result")

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
    assert result.document == mock_from_v1_result.return_value
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
    assert not result.rejected


def test_missing_reviews() -> None:
    with pytest.raises(ResultKeyError):
        Result.from_result(
            {
                "file_version": 1,
                "results": {},
            },
        )


def test_rejected_reviews(mocker: MockerFixture) -> None:
    mocker.patch.object(Document, "_from_v1_result")

    result = Result.from_result(
        {
            "file_version": 1,
            "submission_id": 11,
            "reviews_meta": [
                {
                    "review_id": 66812,
                    "reviewer_id": 422,
                    "review_notes": None,
                    "review_rejected": True,
                    "review_type": "manual",
                },
                {
                    "review_id": 66811,
                    "reviewer_id": 422,
                    "review_notes": None,
                    "review_rejected": False,
                    "review_type": "auto",
                },
            ],
        },
    )

    assert result.rejected is True


def test_accepted_admin_reviews(mocker: MockerFixture) -> None:
    mocker.patch.object(Document, "_from_v1_result")

    result = Result.from_result(
        {
            "file_version": 1,
            "submission_id": 11,
            "reviews_meta": [
                {
                    "review_id": 66813,
                    "reviewer_id": 422,
                    "review_notes": None,
                    "review_rejected": False,
                    "review_type": "admin",
                },
                {
                    "review_id": 66812,
                    "reviewer_id": 422,
                    "review_notes": None,
                    "review_rejected": True,
                    "review_type": "manual",
                },
                {
                    "review_id": 66811,
                    "reviewer_id": 422,
                    "review_notes": None,
                    "review_rejected": False,
                    "review_type": "auto",
                },
            ],
        },
    )

    assert result.rejected is False


def test_rejected_admin_reviews(mocker: MockerFixture) -> None:
    mocker.patch.object(Document, "_from_v1_result")

    result = Result.from_result(
        {
            "file_version": 1,
            "submission_id": 11,
            "reviews_meta": [
                {
                    "review_id": 66813,
                    "reviewer_id": 422,
                    "review_notes": None,
                    "review_rejected": True,
                    "review_type": "admin",
                },
                {
                    "review_id": 66812,
                    "reviewer_id": 422,
                    "review_notes": None,
                    "review_rejected": True,
                    "review_type": "manual",
                },
                {
                    "review_id": 66811,
                    "reviewer_id": 422,
                    "review_notes": None,
                    "review_rejected": False,
                    "review_type": "auto",
                },
            ],
        },
    )

    assert result.rejected is True
