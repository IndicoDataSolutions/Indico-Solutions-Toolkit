import json
from pathlib import Path

import pytest
from indico_toolkit.types import Document, ResultFileError, Submission
from pytest_mock import MockerFixture

data_folder = Path(__file__).parent.parent / "data" / "types"


def test_result_file_version() -> None:
    with pytest.raises(ResultFileError):
        Submission.from_result(
            {
                "file_version": 0,
            },
        )


class TestV1Submission:
    @staticmethod
    @pytest.mark.parametrize("file_path", list(data_folder.glob("*.result.json")))
    def test_from_result(file_path: Path) -> None:
        Submission.from_result(json.loads(file_path.read_text()))

    @staticmethod
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
                    }
                ],
            },
        )

        assert submission.id == 11
        assert submission.version == 1
        assert submission.document == Document._from_v1_result.return_value
        assert len(submission.reviews) == 1
        assert submission.reviews[0].id == 2
        assert submission.rejected is False

    @staticmethod
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

    @staticmethod
    def test_missing_reviews() -> None:
        with pytest.raises(ResultFileError):
            Submission.from_result(
                {
                    "file_version": 1,
                    "results": {},
                },
            )
