from operator import attrgetter

import pytest

from indico_toolkit.results import (
    Classification,
    Document,
    DocumentExtraction,
    Group,
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
def group_alpha() -> Group:
    return Group(id=12345, name="Alpha", index=0)


@pytest.fixture
def group_bravo() -> Group:
    return Group(id=12345, name="Bravo", index=0)


@pytest.fixture
def predictions(
    document: Document,
    classification_model: ModelGroup,
    extraction_model: ModelGroup,
    auto_review: Review,
    manual_review: Review,
    group_alpha: Group,
    group_bravo: Group,
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
                groups={group_alpha},
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
                groups={group_alpha, group_bravo},
            ),
        ]
    )


def test_classifications(predictions: "PredictionList[Prediction]") -> None:
    (classification,) = predictions.classifications
    assert isinstance(classification, Classification)


def test_extractions(predictions: "PredictionList[Prediction]") -> None:
    first_extraction, second_extraction = predictions.extractions
    assert isinstance(first_extraction, DocumentExtraction)
    assert isinstance(second_extraction, DocumentExtraction)


def test_slice_is_prediction_list(predictions: "PredictionList[Prediction]") -> None:
    predictions = predictions[1:3]
    assert len(predictions) == 2
    assert isinstance(predictions, PredictionList)


def test_groupby(
    predictions: "PredictionList[Prediction]", group_alpha: Group, group_bravo: Group
) -> None:
    first_name, last_name = predictions.extractions
    predictions_by_groups = predictions.extractions.groupby(attrgetter("groups"))
    assert predictions_by_groups == {
        frozenset({group_alpha}): [first_name],
        frozenset({group_alpha, group_bravo}): [last_name],
    }


def test_groupbyiter(
    predictions: "PredictionList[Prediction]", group_alpha: Group, group_bravo: Group
) -> None:
    first_name, last_name = predictions.extractions
    predictions_by_group = predictions.extractions.groupbyiter(attrgetter("groups"))
    assert predictions_by_group == {
        group_alpha: [first_name, last_name],
        group_bravo: [last_name],
    }


def test_orderby(predictions: "PredictionList[Prediction]") -> None:
    classification, first_name, last_name = predictions
    predictions = predictions.orderby(attrgetter("confidence"), reverse=True)
    assert predictions == [last_name, first_name, classification]


def test_where_document(
    predictions: "PredictionList[Prediction]", document: Document
) -> None:
    assert predictions.where(document=document) == predictions


def test_where_document_in(
    predictions: "PredictionList[Prediction]", document: Document
) -> None:
    assert predictions.where(document_in={document}) == predictions
    assert predictions.where(document_in={}) == []


def test_where_model(
    predictions: "PredictionList[Prediction]", classification_model: ModelGroup
) -> None:
    (classification,) = predictions.classifications
    assert predictions.where(model=classification_model) == [classification]
    assert predictions.where(model=TaskType.CLASSIFICATION) == [classification]
    assert predictions.where(model="Tax Classification") == [classification]


def test_where_model_in(
    predictions: "PredictionList[Prediction]", classification_model: ModelGroup
) -> None:
    classification, first_name, last_name = predictions
    assert predictions.where(model_in={classification_model}) == [classification]
    assert predictions.where(model_in={TaskType.CLASSIFICATION}) == [classification]
    assert predictions.where(
        model_in={TaskType.CLASSIFICATION, TaskType.DOCUMENT_EXTRACTION}
    ) == [classification, first_name, last_name]
    assert predictions.where(model_in={"Tax Classification"}) == [classification]
    assert predictions.where(
        model_in={"Tax Classification", "1040 Document Extraction"}
    ) == [classification, first_name, last_name]
    assert predictions.where(model_in={}) == []


def test_where_review(
    predictions: "PredictionList[Prediction]", auto_review: Review
) -> None:
    classification, first_name, last_name = predictions
    assert predictions.where(review=None) == [classification]
    assert predictions.where(review=auto_review) == [first_name]
    assert predictions.where(review=ReviewType.MANUAL) == [last_name]

def test_where_review_in(
    predictions: "PredictionList[Prediction]", auto_review: Review
) -> None:
    classification, first_name, last_name = predictions
    assert predictions.where(review_in={None}) == [classification]
    assert predictions.where(
        review_in={None, auto_review}
    ) == [classification, first_name]
    assert predictions.where(
        review_in={auto_review, ReviewType.MANUAL}
    ) == [first_name, last_name]
    assert predictions.where(review_in={}) == []


def test_where_label(predictions: "PredictionList[Prediction]") -> None:
    first_name, _ = predictions.extractions
    assert predictions.where(label="First Name") == [first_name]


def test_where_label_in(predictions: "PredictionList[Prediction]") -> None:
    first_name, last_name = predictions.extractions
    assert predictions.where(
        label_in=("First Name", "Last Name")
    ) == [first_name, last_name]


def test_where_confidence(predictions: "PredictionList[Prediction]") -> None:
    conf_70, conf_80, conf_90 = predictions
    assert predictions.where(min_confidence=0.9) == [conf_90]
    assert predictions.where(min_confidence=0.75, max_confidence=0.85) == [conf_80]
    assert predictions.where(max_confidence=0.7) == [conf_70]


def test_where_page(predictions: "PredictionList[Prediction]") -> None:
    first_name, _ = predictions.extractions
    assert predictions.where(page=0) == [first_name]


def test_where_page_in(predictions: "PredictionList[Prediction]") -> None:
    first_name, last_name = predictions.extractions
    assert predictions.where(page_in=(0, 1)) == [first_name, last_name]


def test_where_accepted(predictions: "PredictionList[Prediction]") -> None:
    first_name, last_name = predictions.extractions
    predictions.unaccept()

    assert predictions.where(accepted=True) == []
    assert predictions.where(accepted=False) == [first_name, last_name]

    predictions.accept()

    assert predictions.where(accepted=False) == []
    assert predictions.where(accepted=True) == [first_name, last_name]

def test_where_rejected(predictions: "PredictionList[Prediction]") -> None:
    first_name, last_name = predictions.extractions
    predictions.unreject()

    assert predictions.where(rejected=True) == []
    assert predictions.where(rejected=False) == [first_name, last_name]

    predictions.reject()

    assert predictions.where(rejected=False) == []
    assert predictions.where(rejected=True) == [first_name, last_name]
