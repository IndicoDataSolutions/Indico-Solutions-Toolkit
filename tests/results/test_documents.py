from pathlib import Path

from indico_toolkit import results
from indico_toolkit.results import (
    ClassificationList,
    ExtractionList,
    PredictionList,
    UnbundlingList,
)

data_folder = Path(__file__).parent.parent / "data" / "results"


def test_v1_document() -> None:
    submission = results.load(
        data_folder / "v1_reviewed_accepted_submission.result_file.json"
    )
    document = submission.document

    assert document.id is None
    assert document.filename is None
    assert (
        document.etl_output
        == "indico-file:///storage/submission/4/11/12/etl_output.json"
    )

    assert document.labels == {
        "Broker City",
        "Broker Contact Email",
        "Broker Contact Name",
        "Broker Name",
        "Broker Phone",
        "Broker State",
        "Broker Street Address",
        "Broker Zip or Postal Code",
        "Description of Operations",
        "Email",
        "Inception Date",
        "Insured City",
        "Insured Name",
        "Insured State",
        "Insured Street Address",
        "Insured Web Address",
        "Insured Zip or Postal Code",
    }
    assert document.models == {"Classification", "Email"}

    assert isinstance(document.pre_review.classifications, ClassificationList)
    assert len(document.pre_review.classifications) == 1

    assert isinstance(document.pre_review.extractions, ExtractionList)
    assert len(document.pre_review.extractions) == 23

    assert isinstance(document.auto_review, PredictionList)
    assert len(document.auto_review) == 0

    assert isinstance(document.manual_review, PredictionList)
    assert len(document.manual_review) == 15

    assert isinstance(document.final, PredictionList)
    assert len(document.final) == 15


def test_v2_document() -> None:
    submission = results.load(
        data_folder / "v2_unreviewed_completed_submission.result_file.json"
    )
    document = submission.documents[0]

    assert document.id == 184
    assert document.filename == "bundle=True.eml"
    assert (
        document.etl_output
        == "indico-file:///storage/submission/4/183/184/etl_output.json"
    )

    assert document.labels == {
        "Broker Contact Email",
        "Broker Contact Name",
        "Broker Name",
        "Description of Operations",
        "Email",
        "Inception Date",
        "Insured City",
        "Insured Name",
        "Insured State",
        "Insured Street Address",
        "Insured Web Address",
        "Insured Zip or Postal Code",
    }
    assert document.models == {"Classification", "Email"}

    assert isinstance(document.pre_review.classifications, ClassificationList)
    assert len(document.pre_review.classifications) == 1

    assert isinstance(document.pre_review.extractions, ExtractionList)
    assert len(document.pre_review.extractions) == 23

    assert isinstance(document.auto_review, PredictionList)
    assert len(document.auto_review) == 0

    assert isinstance(document.manual_review, PredictionList)
    assert len(document.manual_review) == 0

    assert isinstance(document.final, PredictionList)
    assert len(document.final) == 24


def test_v3_document() -> None:
    submission = results.load(
        data_folder / "v3_unreviewed_completed_submission.result_file.json"
    )
    document = submission.document

    assert document.id == 79684
    assert document.filename == "bundled_document.pdf"
    assert (
        document.etl_output
        == "indico-file:///storage/submission/3109/91825/79684/etl_output.json"
    )

    assert document.labels == {
        "BCC",
        "CC",
        "City",
        "Email",
        "Has Vaccine",
        "Name",
        "PFA Indicator",
        "Provider Location",
        "State",
        "Street",
        "Subject",
        "To",
        "Zip",
    }
    assert document.models == {
        "Classify + Unbundle Model",
        "Email Model",
        "Provider Location Model",
    }

    assert isinstance(document.pre_review.unbundlings, UnbundlingList)
    assert len(document.pre_review.unbundlings) == 7

    assert isinstance(document.pre_review.extractions, ExtractionList)
    assert len(document.pre_review.extractions) == 33

    assert isinstance(document.auto_review, PredictionList)
    assert len(document.auto_review) == 0

    assert isinstance(document.manual_review, PredictionList)
    assert len(document.manual_review) == 0

    assert isinstance(document.final, PredictionList)
    assert len(document.final) == 40
