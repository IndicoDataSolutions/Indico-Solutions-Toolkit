from indico_toolkit.results import Review, ReviewType


class TestV1Review:
    @staticmethod
    def test_auto_review() -> None:
        review = Review._from_v1_result(
            {
                "review_id": 1,
                "reviewer_id": 7,
                "review_notes": None,
                "review_rejected": False,
                "review_type": "auto",
            },
        )

        assert review.id == 1
        assert review.reviewer_id == 7
        assert review.notes is None
        assert review.rejected is False
        assert review.type == ReviewType.AUTO

    @staticmethod
    def test_manual_review() -> None:
        review = Review._from_v1_result(
            {
                "review_id": 1,
                "reviewer_id": 7,
                "review_notes": "Rejected For Reasons",
                "review_rejected": True,
                "review_type": "manual",
            },
        )

        assert review.id == 1
        assert review.reviewer_id == 7
        assert review.notes == "Rejected For Reasons"
        assert review.rejected is True
        assert review.type == ReviewType.MANUAL

    @staticmethod
    def test_admin_review() -> None:
        review = Review._from_v1_result(
            {
                "review_id": 1,
                "reviewer_id": 7,
                "review_notes": None,
                "review_rejected": False,
                "review_type": "admin",
            },
        )

        assert review.id == 1
        assert review.reviewer_id == 7
        assert review.notes is None
        assert review.rejected is False
        assert review.type == ReviewType.ADMIN
