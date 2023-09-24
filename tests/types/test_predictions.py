import pytest
from indico_toolkit.types import Classification, Extraction


class TestV1Classification:
    @staticmethod
    def test_pre_review() -> None:
        classification = Classification._from_v1_result(
            "Test Model",
            {
                "confidence": {
                    "Email": 0.5,
                    "Quotation Submission": 0.0,
                    "Liability Insurance Application": 0.0,
                },
                "label": "Email",
            },
        )

        assert classification.model == "Test Model"
        assert classification.label == "Email"
        assert classification.confidence == 0.5
        assert classification.confidences["Email"] == 0.5


class TestV1Extraction:
    @staticmethod
    def test_pre_review() -> None:
        extraction = Extraction._from_v1_result(
            "Test Model",
            {
                "start": 33,
                "end": 62,
                "label": "Insured Name",
                "confidence": {
                    "Insured Name": 0.5,
                    "Insured Street Address": 0.0,
                    "Insured City": 0.0,
                    "Insured State": 0.0,
                    "Insured Zip or Postal Code": 0.0,
                },
                "page_num": 1,
                "text": "Indico Data Solutions",
            },
        )

        assert extraction.model == "Test Model"
        assert extraction.label == "Insured Name"
        assert extraction.text == "Indico Data Solutions"
        assert extraction.confidence == 0.5
        assert extraction.confidences["Insured Name"] == 0.5
        assert extraction.span.start == 33
        assert extraction.span.end == 62
        assert extraction.span.page == 1

    @staticmethod
    def test_post_review() -> None:
        extraction = Extraction._from_v1_result(
            "Test Model",
            {
                "text": "Indico Data Solutions",
                "label": "Insured Name",
                "pageNum": 1,
            },
        )

        assert extraction.model == "Test Model"
        assert extraction.label == "Insured Name"
        assert extraction.text == "Indico Data Solutions"
        assert not extraction.confidences
        assert extraction.span.start is None
        assert extraction.span.end is None
        assert extraction.span.page == 1

        with pytest.raises(AttributeError):
            extraction.confidence
