from indico_toolkit.results import Extraction, Prediction


def test_confidence() -> None:
    prediction = Prediction(
        document=None,  # type: ignore[arg-type]
        model=None,  # type: ignore[arg-type]
        review=None,
        label="Label",
        confidences={"Label": 0.5},
        extras=None,  # type: ignore[arg-type]
    )

    assert prediction.confidence == 0.5
    prediction.confidence = 1.0
    assert prediction.confidence == 1.0


def test_extractions() -> None:
    prediction = Extraction(
        document=None,  # type: ignore[arg-type]
        model=None,  # type: ignore[arg-type]
        review=None,
        label="Label",
        confidences={"Label": 0.5},
        text="Value",
        page=0,
        extras=None,  # type: ignore[arg-type]
        accepted=False,
        rejected=False,
    )

    prediction.reject()
    prediction.accept()
    assert prediction.accepted
    prediction.unaccept()
    assert not prediction.accepted

    prediction.accept()
    prediction.reject()
    assert prediction.rejected
    prediction.unreject()
    assert not prediction.rejected
