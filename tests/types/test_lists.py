import pytest

from indico_toolkit.types import (
    Classification,
    ClassificationList,
    Extraction,
    ExtractionList,
)


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
    def test_model(classifications: ClassificationList) -> None:
        filtered = classifications.where(model="Model A")

        assert isinstance(filtered, ClassificationList)
        assert len(filtered) == 1
        assert filtered[0].model == "Model A"

    @staticmethod
    def test_label(classifications: ClassificationList) -> None:
        filtered = classifications.where(label="Label A")

        assert isinstance(filtered, ClassificationList)
        assert len(filtered) == 1
        assert filtered[0].label == "Label A"

    @staticmethod
    def test_min_confidence(classifications: ClassificationList) -> None:
        filtered = classifications.where(min_confidence=0.75)

        assert isinstance(filtered, ClassificationList)
        assert len(filtered) == 1
        assert filtered[0].confidence == 0.75

    @staticmethod
    def test_max_confidence(classifications: ClassificationList) -> None:
        filtered = classifications.where(max_confidence=0.25)

        assert isinstance(filtered, ClassificationList)
        assert len(filtered) == 1
        assert filtered[0].confidence == 0.25

    @staticmethod
    def test_predicate(classifications: ClassificationList) -> None:
        filtered = classifications.where(predicate=lambda c: 0.4 < c.confidence < 0.6)

        assert isinstance(filtered, ClassificationList)
        assert len(filtered) == 1
        assert filtered[0].confidence == 0.5

    @staticmethod
    def test_multi_chain_where(classifications: ClassificationList) -> None:
        multi_filtered = classifications.where(
            min_confidence=0.4,
            max_confidence=0.6,
        )
        chain_filtered = classifications.where(
            min_confidence=0.4,
        ).where(
            max_confidence=0.6,
        )
        predicate_filtered = classifications.where(
            predicate=lambda c: 0.4 <= c.confidence <= 0.6
        )

        assert isinstance(multi_filtered, ClassificationList)
        assert isinstance(chain_filtered, ClassificationList)
        assert multi_filtered == chain_filtered
        assert multi_filtered == predicate_filtered

    @staticmethod
    def test_apply(classifications: ClassificationList) -> None:
        def reverse(classification: Classification) -> None:
            classification.label = "".join(reversed(classification.label))

        classifications.apply(reverse)

        assert classifications[0].label == "A lebaL"

    @staticmethod
    def test_chain_apply(classifications: ClassificationList) -> None:
        def reverse(classification: Classification) -> None:
            classification.label = "".join(reversed(classification.label))

        def truncate(classification: Classification) -> None:
            classification.label = classification.label[:3]

        classifications.apply(reverse).apply(truncate)

        assert classifications[0].label == "A l"


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
                    [],
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
                    [],
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
                    [],
                ),
            ]
        )

    @staticmethod
    def test_model(extractions: ExtractionList) -> None:
        filtered = extractions.where(model="Model A")

        assert isinstance(filtered, ExtractionList)
        assert len(filtered) == 1
        assert filtered[0].model == "Model A"

    @staticmethod
    def test_label(extractions: ExtractionList) -> None:
        filtered = extractions.where(label="Label A")

        assert isinstance(filtered, ExtractionList)
        assert len(filtered) == 1
        assert filtered[0].label == "Label A"

    @staticmethod
    def test_min_confidence(extractions: ExtractionList) -> None:
        filtered = extractions.where(min_confidence=0.75)

        assert isinstance(filtered, ExtractionList)
        assert len(filtered) == 1
        assert filtered[0].confidence == 0.75

    @staticmethod
    def test_max_confidence(extractions: ExtractionList) -> None:
        filtered = extractions.where(max_confidence=0.25)

        assert isinstance(filtered, ExtractionList)
        assert len(filtered) == 1
        assert filtered[0].confidence == 0.25

    @staticmethod
    def test_predicate(extractions: ExtractionList) -> None:
        filtered = extractions.where(predicate=lambda e: 0.4 < e.confidence < 0.6)

        assert isinstance(filtered, ExtractionList)
        assert len(filtered) == 1
        assert filtered[0].confidence == 0.5

    @staticmethod
    def test_multi_chain_where(extractions: ExtractionList) -> None:
        multi_filtered = extractions.where(
            min_confidence=0.4,
            max_confidence=0.6,
        )
        chain_filtered = extractions.where(
            min_confidence=0.4,
        ).where(
            max_confidence=0.6,
        )
        predicate_filtered = extractions.where(
            predicate=lambda e: 0.4 <= e.confidence <= 0.6
        )

        assert isinstance(multi_filtered, ExtractionList)
        assert isinstance(chain_filtered, ExtractionList)
        assert multi_filtered == chain_filtered
        assert multi_filtered == predicate_filtered

    @staticmethod
    def test_apply(extractions: ExtractionList) -> None:
        def reverse(extraction: Extraction) -> None:
            extraction.text = "".join(reversed(extraction.text))

        extractions.apply(reverse)

        assert extractions[0].text == "A txeT"

    @staticmethod
    def test_chain_apply(extractions: ExtractionList) -> None:
        def reverse(extraction: Extraction) -> None:
            extraction.text = "".join(reversed(extraction.text))

        def truncate(extraction: Extraction) -> None:
            extraction.text = extraction.text[:3]

        extractions.apply(reverse).apply(truncate)

        assert extractions[0].text == "A t"

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
