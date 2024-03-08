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
    result = results.load(
        data_folder / "v1_classify_extract_complete_accepted_with_meta.json"
    )
    document = result.document

    assert document.file_id is None
    assert document.filename is None
    assert (
        document.etl_output_url
        == "indico-file:///storage/submission/3388/93505/81364/etl_output.json"
    )
    assert (
        document.full_text_url
        == "indico-file:///storage/submission/3388/93505/81364/full_text.txt"
    )

    assert document.labels == {
        "Invoice Date",
        "Invoice Number",
        "Invoice Subtotal",
        "Invoice Tax",
        "Invoice Total",
        "Invoice",
        "Line Item Name",
        "Line Item Quantity",
        "Line Item Total",
        "Vendor Name",
    }
    assert document.models == {
        "Accounting Classification Model",
        "Invoice Extraction Model",
    }

    assert isinstance(document.pre_review.classifications, ClassificationList)
    assert len(document.pre_review.classifications) == 1

    assert isinstance(document.pre_review.extractions, ExtractionList)
    assert len(document.pre_review.extractions) == 13

    assert isinstance(document.auto_review, PredictionList)
    assert len(document.auto_review) == 14

    assert isinstance(document.manual_review, PredictionList)
    assert len(document.manual_review) == 16

    assert isinstance(document.final, PredictionList)
    assert len(document.final) == 16


def test_v2_document() -> None:
    result = results.load(data_folder / "v2_classify_extract_multifile_complete.json")
    document = result.documents[0]

    assert document.file_id == 81369
    assert document.filename == "invoice.pdf"
    assert (
        document.etl_output_url
        == "indico-file:///storage/submission/3388/93510/81369/etl_output.json"
    )
    assert (
        document.full_text_url
        == "indico-file:///storage/submission/3388/93510/81369/full_text.txt"
    )

    assert document.labels == {
        "Invoice Date",
        "Invoice Number",
        "Invoice Subtotal",
        "Invoice Tax",
        "Invoice Total",
        "Invoice",
        "Line Item Name",
        "Line Item Quantity",
        "Line Item Total",
        "Vendor Name",
    }
    assert document.models == {
        "Accounting Classification Model",
        "Invoice Extraction Model",
    }

    assert isinstance(document.pre_review.classifications, ClassificationList)
    assert len(document.pre_review.classifications) == 1

    assert isinstance(document.pre_review.extractions, ExtractionList)
    assert len(document.pre_review.extractions) == 13

    assert isinstance(document.auto_review, PredictionList)
    assert len(document.auto_review) == 0

    assert isinstance(document.manual_review, PredictionList)
    assert len(document.manual_review) == 0

    assert isinstance(document.final, PredictionList)
    assert len(document.final) == 14


def test_v3_document() -> None:
    result = results.load(data_folder / "v3_classify_unbundle_extract_complete.json")
    document = result.document

    assert document.file_id == 81371
    assert document.filename == "invoice_purchase_order.pdf"
    assert (
        document.etl_output_url
        == "indico-file:///storage/submission/3390/93511/81371/etl_output.json"
    )
    assert (
        document.full_text_url
        == "indico-file:///storage/submission/3390/93511/81371/full_text.txt"
    )

    assert document.labels == {
        "Buyer ID",
        "Buyer Name",
        "Invoice Date",
        "Invoice Number",
        "Invoice Subtotal",
        "Invoice Tax",
        "Invoice Total",
        "Invoice",
        "Line Item Name",
        "Line Item Quantity",
        "Line Item Total",
        "PO Date",
        "PO Number",
        "PO Total",
        "Product Code",
        "Product Description",
        "Product Quantity",
        "Product Total",
        "Product Unit Cost",
        "Purchase Order",
        "Vendor Name",
    }
    assert document.models == {
        "Accounting Classify + Unbundle Model",
        "Invoice Extraction Model",
        "Purchase Order Extraction Model",
    }

    assert isinstance(document.pre_review.unbundlings, UnbundlingList)
    assert len(document.pre_review.unbundlings) == 2

    assert isinstance(document.pre_review.extractions, ExtractionList)
    assert len(document.pre_review.extractions) == 29

    assert isinstance(document.auto_review, PredictionList)
    assert len(document.auto_review) == 0

    assert isinstance(document.manual_review, PredictionList)
    assert len(document.manual_review) == 0

    assert isinstance(document.final, PredictionList)
    assert len(document.final) == 31
