from operator import attrgetter

import pytest

from indico_toolkit.results import (
    Classification,
    Document,
    DocumentExtraction,
    ModelGroup,
    Prediction,
    PredictionList,
    Review,
    ReviewType,
    TaskType,
)


@pytest.fixture
def document() -> Document:
    return Document(
        id=2922,
        name="1040_filled.tiff",
        etl_output_url="indico-file:///storage/submission/2922/etl_output.json",
        full_text_url="indico-file:///storage/submission/2922/full_text.txt",
        _model_sections=frozenset({"124", "123", "122", "121"}),
    )


@pytest.fixture
def classification_model() -> ModelGroup:
    return ModelGroup(
        id=121, name="Tax Classification", task_type=TaskType.CLASSIFICATION
    )


@pytest.fixture
def extraction_model() -> ModelGroup:
    return ModelGroup(
        id=122, name="1040 Document Extraction", task_type=TaskType.DOCUMENT_EXTRACTION
    )


@pytest.fixture
def auto_review() -> Review:
    return Review(
        id=1306, reviewer_id=5, notes="", rejected=False, type=ReviewType.AUTO
    )


@pytest.fixture
def manual_review() -> Review:
    return Review(
        id=1308, reviewer_id=5, notes="", rejected=False, type=ReviewType.MANUAL
    )


@pytest.fixture
def predictions(
    document: Document,
    classification_model: ModelGroup,
    extraction_model: ModelGroup,
    auto_review: Review,
    manual_review: Review,
) -> "PredictionList[Prediction]":
    return PredictionList(
        [
            Classification(
                document=document,
                model=classification_model,
                review=None,
                label="1040",
                confidences={"1040": 0.7},
                extras={},
            ),
            DocumentExtraction(
                document=document,
                model=extraction_model,
                review=auto_review,
                label="First Name",
                confidences={"First Name": 0.8},
                extras={},
                accepted=False,
                rejected=False,
                text="John",
                start=352,
                end=356,
                page=0,
                groups=set(),
            ),
            DocumentExtraction(
                document=document,
                model=extraction_model,
                review=manual_review,
                label="Last Name",
                confidences={"Last Name": 0.9},
                extras={},
                accepted=False,
                rejected=False,
                text="Doe",
                start=357,
                end=360,
                page=1,
                groups=set(),
            ),
        ]
    )


def test_classifications(predictions: "PredictionList[Prediction]") -> None:
    (classification,) = predictions.classifications
    assert isinstance(classification, Classification)


def test_extractions(predictions: "PredictionList[Prediction]") -> None:
    (first_extraction, second_extraction) = predictions.document_extractions
    assert isinstance(first_extraction, DocumentExtraction)
    assert isinstance(second_extraction, DocumentExtraction)


def test_slice_is_prediction_list(predictions: "PredictionList[Prediction]") -> None:
    predictions = predictions[1:3]
    assert len(predictions) == 2
    assert isinstance(predictions, PredictionList)


def test_orderby(predictions: "PredictionList[Prediction]") -> None:
    predictions = predictions.orderby(attrgetter("confidence"), reverse=True)
    assert predictions[0].confidence == 0.9


def test_where_document(
    predictions: "PredictionList[Prediction]", document: Document
) -> None:
    assert predictions.where(document=document) == predictions


def test_where_model(
    predictions: "PredictionList[Prediction]", classification_model: ModelGroup
) -> None:
    classification, first_name, last_name = predictions

    filtered = predictions.where(model=classification_model)
    assert classification in filtered
    assert first_name not in filtered
    assert last_name not in filtered

    filtered = predictions.where(model=TaskType.CLASSIFICATION)
    assert classification in filtered
    assert first_name not in filtered
    assert last_name not in filtered

    filtered = predictions.where(model="Tax Classification")
    assert classification in filtered
    assert first_name not in filtered
    assert last_name not in filtered


def test_where_label(predictions: "PredictionList[Prediction]") -> None:
    classification, first_name, last_name = predictions

    filtered = predictions.where(label="First Name")
    assert classification not in filtered
    assert first_name in filtered
    assert last_name not in filtered

    filtered = predictions.where(label_in=("First Name", "Last Name"))
    assert classification not in filtered
    assert first_name in filtered
    assert last_name in filtered


def test_where_confidence(predictions: "PredictionList[Prediction]") -> None:
    conf_70, conf_80, conf_90 = predictions

    filtered = predictions.where(min_confidence=0.9)
    assert conf_70 not in filtered
    assert conf_80 not in filtered
    assert conf_90 in filtered

    filtered = predictions.where(min_confidence=0.75, max_confidence=0.85)
    assert conf_70 not in filtered
    assert conf_80 in filtered
    assert conf_90 not in filtered

    filtered = predictions.where(max_confidence=0.7)
    assert conf_70 in filtered
    assert conf_80 not in filtered
    assert conf_90 not in filtered


def test_where_page(predictions: "PredictionList[Prediction]") -> None:
    classification, first_name, last_name = predictions

    filtered = predictions.where(page=0)
    assert classification not in filtered
    assert first_name in filtered
    assert last_name not in filtered

    filtered = predictions.where(page_in=(0, 1))
    assert classification not in filtered
    assert first_name in filtered
    assert last_name in filtered


def test_where_accepted(predictions: "PredictionList[Prediction]") -> None:
    _, first_name, last_name = predictions
    predictions.unaccept()

    filtered = predictions.where(accepted=True)
    assert first_name not in filtered
    assert last_name not in filtered

    filtered = predictions.where(accepted=False)
    assert first_name in filtered
    assert last_name in filtered

    predictions.accept()

    filtered = predictions.where(accepted=False)
    assert first_name not in filtered
    assert last_name not in filtered

    filtered = predictions.where(accepted=True)
    assert first_name in filtered
    assert last_name in filtered


def test_where_rejected(predictions: "PredictionList[Prediction]") -> None:
    _, first_name, last_name = predictions
    predictions.unreject()

    filtered = predictions.where(rejected=True)
    assert first_name not in filtered
    assert last_name not in filtered

    filtered = predictions.where(rejected=False)
    assert first_name in filtered
    assert last_name in filtered

    predictions.reject()

    filtered = predictions.where(rejected=False)
    assert first_name not in filtered
    assert last_name not in filtered

    filtered = predictions.where(rejected=True)
    assert first_name in filtered
    assert last_name in filtered
