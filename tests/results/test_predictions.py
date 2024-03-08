import pytest

from indico_toolkit.results import Classification, Extraction, Unbundling


class TestClassification:
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
        assert not classification.extras

    @staticmethod
    def test_extras() -> None:
        classification = Classification._from_v1_result(
            "Test Model",
            {
                "confidence": {},
                "label": "",
                "some_other_field": 123,
            },
        )

        assert isinstance(classification.extras, dict)
        assert classification.extras["some_other_field"] == 123


class TestExtraction:
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
        assert not extraction.extras

    @staticmethod
    def test_extras() -> None:
        extraction = Extraction._from_v1_result(
            "Test Model",
            {
                "confidence": {},
                "label": "",
                "page_num": 0,
                "text": "",
                "some_other_field": 123,
            },
        )

        assert isinstance(extraction.extras, dict)
        assert extraction.extras["some_other_field"] == 123

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
        assert not extraction.extras

        with pytest.raises(AttributeError):
            extraction.confidence

    @staticmethod
    def test_accept_reject() -> None:
        extraction = Extraction("", "", {}, {}, "", [])

        assert not extraction.accepted
        assert not extraction.rejected

        extraction.accept()

        assert extraction.accepted
        assert not extraction.rejected

        extraction.unaccept()

        assert not extraction.accepted
        assert not extraction.rejected

        extraction.accept()
        extraction.reject()

        assert not extraction.accepted
        assert extraction.rejected

        extraction.unreject()

        assert not extraction.accepted
        assert not extraction.rejected

        extraction.reject()
        extraction.accept()

        assert extraction.accepted
        assert not extraction.rejected

    @staticmethod
    def test_no_typed_entities() -> None:
        original_value = "2024-02-29"
        updated_value = "2024-03-01"

        extraction = Extraction._from_v1_result(
            "Test Model",
            {
                "start": 33,
                "end": 43,
                "label": "Date",
                "confidence": {
                    "Date": 0.5,
                },
                "page_num": 1,
                "text": original_value,
            },
        )

        assert extraction.text == original_value

        extraction.text = updated_value

        assert extraction._to_changes()["text"] == updated_value

    @staticmethod
    def test_typed_entities() -> None:
        original_value = "2024-02-29"
        updated_value = "2024-03-01"
        formatted_value = "03/01/2024"

        extraction = Extraction._from_v1_result(
            "Test Model",
            {
                "start": 33,
                "end": 43,
                "label": "Date",
                "confidence": {
                    "Date": 0.5,
                },
                "page_num": 1,
                "text": original_value,
                "normalized": {
                    "text": original_value,
                    "formatted": formatted_value,
                },
            },
        )

        assert extraction.text == original_value
        assert extraction.extras["normalized"]["text"] == original_value
        assert extraction.extras["normalized"]["formatted"] == formatted_value

        changes = extraction._to_changes()

        assert changes["text"] == original_value
        assert changes["normalized"]["text"] == original_value
        assert changes["normalized"]["formatted"] == formatted_value

        extraction.text = updated_value
        changes = extraction._to_changes()

        assert changes["text"] == updated_value
        assert changes["normalized"]["text"] == updated_value
        assert changes["normalized"]["formatted"] == updated_value


class TestUnbundling:
    @staticmethod
    def test_pre_review() -> None:
        unbunlding = Unbundling._from_v3_result(
            "Test Model",
            {
                "label": "Email",
                "confidence": {
                    "Email": 0.5,
                    "Provider Location": 0.024194885045289993,
                },
                "spans": [{"start": 0, "end": 155, "page_num": 0}],
            },
        )

        assert unbunlding.model == "Test Model"
        assert unbunlding.label == "Email"
        assert unbunlding.confidence == 0.5
        assert unbunlding.confidences["Email"] == 0.5
        assert unbunlding.span.start == 0
        assert unbunlding.span.end == 155
        assert unbunlding.span.page == 0
        assert not unbunlding.extras

    @staticmethod
    def test_extras() -> None:
        unbunlding = Unbundling._from_v3_result(
            "Test Model",
            {
                "confidence": {},
                "label": "",
                "spans": [],
                "some_other_field": 123,
            },
        )

        assert isinstance(unbunlding.extras, dict)
        assert unbunlding.extras["some_other_field"] == 123
