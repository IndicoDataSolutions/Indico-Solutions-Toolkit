import pytest
import os
import pickle
import tempfile
import fitz
from indico_toolkit.highlighter import Highlighter
from indico_toolkit.ocr import OnDoc

# TODO: test different colored highlights


@pytest.fixture(scope="session")
def highlighter_data_path(testdir_file_path):
    return os.path.join(testdir_file_path, "highlighter/data/")


@pytest.fixture(scope="session")
def highlighter_pdf_path(highlighter_data_path):
    return os.path.join(highlighter_data_path, "invoice_sample.pdf")


@pytest.fixture(scope="session")
def invoice_ocr_obj(highlighter_data_path):
    return pickle.load(open(os.path.join(highlighter_data_path, "ocr_obj.p"), "rb"))


@pytest.fixture(scope="session")
def invoice_predictions(highlighter_data_path):
    return pickle.load(open(os.path.join(highlighter_data_path, "predictions.p"), "rb"))


def test_highlighter_collect_tokens(
    invoice_predictions, invoice_ocr_obj, highlighter_pdf_path
):
    highlight = Highlighter(invoice_predictions, highlighter_pdf_path)
    highlight.collect_tokens(invoice_ocr_obj.token_objects)
    assert len(highlight._errored_predictions) == 0
    assert isinstance(highlight._mapped_positions, list)
    assert isinstance(highlight._mapped_positions[0], dict)
    assert "label" in highlight._mapped_positions[0]
    assert "position" in highlight._mapped_positions[0]
    assert "prediction_index" in highlight._mapped_positions[0]
    assert isinstance(highlight.mapped_positions_by_page, dict)
    assert 1 in highlight.mapped_positions_by_page
    assert 0 in highlight.mapped_positions_by_page
    assert isinstance(highlight.mapped_positions_by_page[0], list)
    assert isinstance(highlight.mapped_positions_by_page[0][0], dict)


def test_highlighter_highlight_pdf(
    invoice_predictions, invoice_ocr_obj, highlighter_pdf_path
):
    highlight = Highlighter(invoice_predictions, highlighter_pdf_path)
    highlight.collect_tokens(invoice_ocr_obj.token_objects)
    number_of_tokens_to_highlight = len(highlight._mapped_positions)
    with tempfile.NamedTemporaryFile(suffix=".pdf") as f:
        highlight.highlight_pdf(f.name, invoice_ocr_obj.page_heights_and_widths)
        doc = fitz.open(f.name)
        num_highlights = sum([1 for page in doc for annotation in page.annots()])
        assert num_highlights == number_of_tokens_to_highlight


def test__get_page_label_counts(
    invoice_predictions, invoice_ocr_obj, highlighter_pdf_path
):
    highlight = Highlighter(invoice_predictions, highlighter_pdf_path)
    highlight.collect_tokens(invoice_ocr_obj.token_objects)
    label_counts = highlight._get_page_label_counts(highlight._mapped_positions)
    assert label_counts["Vendor"] == 1
    assert label_counts["Line Item Value"] == 11
    assert label_counts["Line Item"] == 14
    assert label_counts["Total"] == 1
    assert label_counts["Invoice Number"] == 1


def test__get_toc_text(invoice_predictions, invoice_ocr_obj, highlighter_pdf_path):
    highlight = Highlighter(invoice_predictions, highlighter_pdf_path)
    highlight.collect_tokens(invoice_ocr_obj.token_objects)
    toc_text = highlight._get_toc_text()
    assert isinstance(toc_text, str)
    assert "Page 1" in toc_text
    assert "Page 2" in toc_text
    assert "Vendor (1)" in toc_text
    assert "File: invoice_sample.pdf" in toc_text


def test_table_of_contents(invoice_predictions, invoice_ocr_obj, highlighter_pdf_path):
    highlight = Highlighter(invoice_predictions, highlighter_pdf_path)
    highlight.collect_tokens(invoice_ocr_obj.token_objects)
    number_of_tokens_to_highlight = len(highlight._mapped_positions)
    with tempfile.NamedTemporaryFile(suffix=".pdf") as f:
        highlight.highlight_pdf(
            f.name, invoice_ocr_obj.page_heights_and_widths, include_toc=True
        )
        doc = fitz.open(f.name)
        assert doc.page_count == 3
        num_highlights = sum([1 for page in doc for annotation in page.annots()])
        assert num_highlights == number_of_tokens_to_highlight
        toc_text = doc[0].get_textpage().extractText()
        assert "File: invoice_sample.pdf" in toc_text
