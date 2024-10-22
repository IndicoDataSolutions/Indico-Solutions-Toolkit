from indico_toolkit.results import Result, Review


def test_rejected() -> None:
    result = Result(
        version=None,  # type: ignore[arg-type]
        submission_id=None,  # type: ignore[arg-type]
        documents=None,  # type: ignore[arg-type]
        models=None,  # type: ignore[arg-type]
        predictions=None,  # type: ignore[arg-type]
        reviews=[
            Review(
                id=None,  # type: ignore[arg-type]
                reviewer_id=None,  # type: ignore[arg-type]
                notes=None,  # type: ignore[arg-type]
                rejected=True,
                type=None,  # type: ignore[arg-type]
            ),
        ],
    )

    assert result.rejected


def test_unrejected() -> None:
    result = Result(
        version=None,  # type: ignore[arg-type]
        submission_id=None,  # type: ignore[arg-type]
        documents=None,  # type: ignore[arg-type]
        models=None,  # type: ignore[arg-type]
        predictions=None,  # type: ignore[arg-type]
        reviews=[
            Review(
                id=None,  # type: ignore[arg-type]
                reviewer_id=None,  # type: ignore[arg-type]
                notes=None,  # type: ignore[arg-type]
                rejected=False,
                type=None,  # type: ignore[arg-type]
            ),
            Review(
                id=None,  # type: ignore[arg-type]
                reviewer_id=None,  # type: ignore[arg-type]
                notes=None,  # type: ignore[arg-type]
                rejected=True,
                type=None,  # type: ignore[arg-type]
            ),
            Review(
                id=None,  # type: ignore[arg-type]
                reviewer_id=None,  # type: ignore[arg-type]
                notes=None,  # type: ignore[arg-type]
                rejected=False,
                type=None,  # type: ignore[arg-type]
            ),
        ],
    )

    assert not result.rejected
