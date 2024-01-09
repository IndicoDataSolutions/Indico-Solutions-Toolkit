from operator import attrgetter

import pytest

from indico_toolkit.results import (
    Classification,
    ClassificationList,
    Extraction,
    ExtractionList,
    Prediction,
    PredictionList,
    Span,
)


class TestPredictionList:
    @staticmethod
    @pytest.fixture
    def predictions() -> PredictionList:
        return PredictionList(
            [
                Classification(
                    "Model A",
                    "Label A",
                    {
                        "Label A": 0.25,
                        "Label B": 0.5,
                        "Label C": 0.75,
                    },
                    {},
                ),
                Extraction(
                    "Model B",
                    "Label B",
                    {
                        "Label A": 0.25,
                        "Label B": 0.5,
                        "Label C": 0.75,
                    },
                    {},
                    "Text B",
                    [Span(page=0, start=1, end=2)],
                ),
                Extraction(
                    "Model C",
                    "Label C",
                    {
                        "Label A": 0.25,
                        "Label B": 0.5,
                        "Label C": 0.75,
                    },
                    {},
                    "Text C",
                    [Span(page=0, start=1, end=2)],
                ),
            ]
        )

    @staticmethod
    def test_classification(predictions: PredictionList) -> None:
        assert isinstance(predictions.classification, Classification)

    @staticmethod
    def test_classifications(predictions: PredictionList) -> None:
        classifications = predictions.classifications

        assert isinstance(classifications, ClassificationList)
        assert len(classifications) == 1

    @staticmethod
    def test_extractions(predictions: PredictionList) -> None:
        extractions = predictions.extractions

        assert isinstance(extractions, ExtractionList)
        assert len(extractions) == 2

    @staticmethod
    def test_labels(predictions: PredictionList) -> None:
        assert predictions.labels == {"Label A", "Label B", "Label C"}

    @staticmethod
    def test_models(predictions: PredictionList) -> None:
        assert predictions.models == {"Model A", "Model B", "Model C"}

    @staticmethod
    def test_apply(predictions: PredictionList) -> None:
        def reverse(prediction: Prediction) -> None:
            prediction.label = "".join(reversed(prediction.label))

        predictions.apply(reverse)

        assert predictions[0].label == "A lebaL"

    @staticmethod
    def test_apply_chain(predictions: PredictionList) -> None:
        def reverse(prediction: Prediction) -> None:
            prediction.label = "".join(reversed(prediction.label))

        def truncate(prediction: Prediction) -> None:
            prediction.label = prediction.label[:3]

        predictions.apply(reverse).apply(truncate)

        assert predictions[0].label == "A l"

    @staticmethod
    def test_groupby(predictions: PredictionList) -> None:
        groups = predictions.groupby(attrgetter("label"))

        assert len(tuple(groups.keys())) == 3
        assert len(groups["Label A"]) == 1
        assert groups["Label A"][0].label == "Label A"

    @staticmethod
    def test_orderby(predictions: PredictionList) -> None:
        ordered = predictions.orderby(attrgetter("confidence"), reverse=True)

        assert ordered[0].confidence == 0.75

    @staticmethod
    def test_orderby_no_in_place_sort(predictions: PredictionList) -> None:
        with pytest.raises(RuntimeError):
            predictions.sort()

    @staticmethod
    def test_to_changes(predictions: PredictionList) -> None:
        assert predictions.to_changes() == {
            "Model A": {
                "confidence": {"Label A": 0.25, "Label B": 0.5, "Label C": 0.75},
                "label": "Label A",
            },
            "Model B": [
                {
                    "confidence": {"Label A": 0.25, "Label B": 0.5, "Label C": 0.75},
                    "end": 2,
                    "label": "Label B",
                    "page_num": 0,
                    "start": 1,
                    "text": "Text B",
                }
            ],
            "Model C": [
                {
                    "confidence": {"Label A": 0.25, "Label B": 0.5, "Label C": 0.75},
                    "end": 2,
                    "label": "Label C",
                    "page_num": 0,
                    "start": 1,
                    "text": "Text C",
                }
            ],
        }

    @staticmethod
    def test_where_model(predictions: PredictionList) -> None:
        filtered = predictions.where(model="Model A")

        assert isinstance(filtered, PredictionList)
        assert len(filtered) == 1
        assert filtered[0].model == "Model A"

    @staticmethod
    def test_where_label(predictions: PredictionList) -> None:
        filtered = predictions.where(label="Label A")

        assert isinstance(filtered, PredictionList)
        assert len(filtered) == 1
        assert filtered[0].label == "Label A"

    @staticmethod
    def test_where_min_confidence(predictions: PredictionList) -> None:
        filtered = predictions.where(min_confidence=0.75)

        assert isinstance(filtered, PredictionList)
        assert len(filtered) == 1
        assert filtered[0].confidence == 0.75

    @staticmethod
    def test_where_max_confidence(predictions: PredictionList) -> None:
        filtered = predictions.where(max_confidence=0.25)

        assert isinstance(filtered, PredictionList)
        assert len(filtered) == 1
        assert filtered[0].confidence == 0.25

    @staticmethod
    def test_where_predicate(predictions: PredictionList) -> None:
        filtered = predictions.where(predicate=lambda pred: 0.4 < pred.confidence < 0.6)

        assert isinstance(filtered, PredictionList)
        assert len(filtered) == 1
        assert filtered[0].confidence == 0.5

    @staticmethod
    def test_where_multi_chain(predictions: PredictionList) -> None:
        multi_filtered = predictions.where(
            min_confidence=0.4,
            max_confidence=0.6,
        )
        chain_filtered = predictions.where(
            min_confidence=0.4,
        ).where(
            max_confidence=0.6,
        )
        predicate_filtered = predictions.where(
            predicate=lambda pred: 0.4 <= pred.confidence <= 0.6
        )

        assert isinstance(multi_filtered, PredictionList)
        assert isinstance(chain_filtered, PredictionList)
        assert multi_filtered == chain_filtered
        assert multi_filtered == predicate_filtered


class TestClassificationList:
    @staticmethod
    @pytest.fixture
    def classifications() -> ClassificationList:
        return ClassificationList(
            [
                Classification(
                    "Model A",
                    "Label A",
                    {
                        "Label A": 0.25,
                        "Label B": 0.5,
                        "Label C": 0.75,
                    },
                    {},
                ),
                Classification(
                    "Model B",
                    "Label B",
                    {
                        "Label A": 0.25,
                        "Label B": 0.5,
                        "Label C": 0.75,
                    },
                    {},
                ),
                Classification(
                    "Model C",
                    "Label C",
                    {
                        "Label A": 0.25,
                        "Label B": 0.5,
                        "Label C": 0.75,
                    },
                    {},
                ),
            ]
        )

    @staticmethod
    def test_groupby_return_type(classifications: ClassificationList) -> None:
        groups = classifications.groupby(attrgetter("label"))

        assert isinstance(groups["Label A"], ClassificationList)

    @staticmethod
    def test_orderby_return_type(classifications: ClassificationList) -> None:
        ordered = classifications.orderby(attrgetter("confidence"), reverse=True)

        assert isinstance(ordered, ClassificationList)

    @staticmethod
    def test_to_changes(classifications: ClassificationList) -> None:
        assert classifications.to_changes() == {
            "Model A": {
                "confidence": {"Label A": 0.25, "Label B": 0.5, "Label C": 0.75},
                "label": "Label A",
            },
            "Model B": {
                "confidence": {"Label A": 0.25, "Label B": 0.5, "Label C": 0.75},
                "label": "Label B",
            },
            "Model C": {
                "confidence": {"Label A": 0.25, "Label B": 0.5, "Label C": 0.75},
                "label": "Label C",
            },
        }

    @staticmethod
    def test_where_return_type(classifications: ClassificationList) -> None:
        filtered = classifications.where(predicate=lambda _: True)

        assert isinstance(filtered, ClassificationList)


class TestExtractionList:
    @staticmethod
    @pytest.fixture
    def extractions() -> ExtractionList:
        return ExtractionList(
            [
                Extraction(
                    "Model A",
                    "Label A",
                    {
                        "Label A": 0.25,
                        "Label B": 0.5,
                        "Label C": 0.75,
                    },
                    {},
                    "Text A",
                    [Span(page=0, start=1, end=2)],
                ),
                Extraction(
                    "Model B",
                    "Label B",
                    {
                        "Label A": 0.25,
                        "Label B": 0.5,
                        "Label C": 0.75,
                    },
                    {},
                    "Text B",
                    [Span(page=0, start=1, end=2)],
                ),
                Extraction(
                    "Model C",
                    "Label C",
                    {
                        "Label A": 0.25,
                        "Label B": 0.5,
                        "Label C": 0.75,
                    },
                    {},
                    "Text C",
                    [Span(page=0, start=1, end=2)],
                ),
            ]
        )

    @staticmethod
    def test_accept_reject(extractions: ExtractionList) -> None:
        assert not extractions[0].accepted
        assert not extractions[0].rejected

        extractions.accept()

        assert extractions[0].accepted
        assert not extractions[0].rejected

        extractions.reject()

        assert not extractions[0].accepted
        assert extractions[0].rejected

    @staticmethod
    def test_groupby_return_type(extractions: ExtractionList) -> None:
        groups = extractions.groupby(attrgetter("label"))

        assert isinstance(groups["Label A"], ExtractionList)

    @staticmethod
    def test_orderby_return_type(extractions: ExtractionList) -> None:
        ordered = extractions.orderby(attrgetter("confidence"), reverse=True)

        assert isinstance(ordered, ExtractionList)

    @staticmethod
    def test_to_changes(extractions: ExtractionList) -> None:
        assert extractions.to_changes() == {
            "Model A": [
                {
                    "confidence": {"Label A": 0.25, "Label B": 0.5, "Label C": 0.75},
                    "end": 2,
                    "label": "Label A",
                    "page_num": 0,
                    "start": 1,
                    "text": "Text A",
                }
            ],
            "Model B": [
                {
                    "confidence": {"Label A": 0.25, "Label B": 0.5, "Label C": 0.75},
                    "end": 2,
                    "label": "Label B",
                    "page_num": 0,
                    "start": 1,
                    "text": "Text B",
                }
            ],
            "Model C": [
                {
                    "confidence": {"Label A": 0.25, "Label B": 0.5, "Label C": 0.75},
                    "end": 2,
                    "label": "Label C",
                    "page_num": 0,
                    "start": 1,
                    "text": "Text C",
                }
            ],
        }

    @staticmethod
    def test_where_return_type(extractions: ExtractionList) -> None:
        filtered = extractions.where(predicate=lambda _: True)

        assert isinstance(filtered, ExtractionList)
