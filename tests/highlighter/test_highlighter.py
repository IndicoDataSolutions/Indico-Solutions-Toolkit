import pytest
import os
import pickle
import tempfile
import fitz
from indico_toolkit.highlighter import Highlighter


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


def test_highlighter_bookmarking(
    invoice_predictions, invoice_ocr_obj, highlighter_pdf_path
):
    highlight = Highlighter(invoice_predictions, highlighter_pdf_path)
    highlight.collect_tokens(invoice_ocr_obj.token_objects)
    with tempfile.NamedTemporaryFile(suffix=".pdf") as f:
        highlight.highlight_pdf(f.name, invoice_ocr_obj.page_heights_and_widths)
        doc = fitz.open(f.name)
        toc = doc.getToC()
        assert len(toc) == 7
        # 5 first page labels
        assert len([i for i in toc if i[2] == 1]) == 5
        # 2 unique second page labels
        assert len([i for i in toc if i[2] == 2]) == 2

@pytest.mark.parametrize("all_yellow_bool, unique_color_count", [(True, 1), (False, 5)])
def test_highlight_colors(
    invoice_predictions,
    invoice_ocr_obj,
    highlighter_pdf_path,
    all_yellow_bool,
    unique_color_count,
):
    highlight = Highlighter(invoice_predictions, highlighter_pdf_path)
    highlight.collect_tokens(invoice_ocr_obj.token_objects)
    with tempfile.NamedTemporaryFile(suffix=".pdf") as f:
        highlight.highlight_pdf(
            f.name,
            invoice_ocr_obj.page_heights_and_widths,
            all_yellow_highlight=all_yellow_bool,
        )
        doc = fitz.open(f.name)
        highlight_colors = set(
            [str(i.colors["stroke"]) for page in doc for i in page.annots()]
        )
        assert len(highlight_colors) == unique_color_count


def test_get_label_color_hash():
    highlight = Highlighter(
        [{"label": "a", "text": "b"}, {"label": "b", "text": "a"}], "something.pdf"
    )
    color_hash = highlight.get_label_color_hash()
    assert isinstance(color_hash, dict)
    assert len(color_hash) == 2
    assert "a" in color_hash.keys() and "b" in color_hash.keys()


def test_add_label_annotations(
    invoice_predictions,
    invoice_ocr_obj,
    highlighter_pdf_path,
):
    highlight = Highlighter(invoice_predictions, highlighter_pdf_path)
    highlight.collect_tokens(invoice_ocr_obj.token_objects)
    with tempfile.NamedTemporaryFile(suffix=".pdf") as f:
        highlight.highlight_pdf(
            f.name,
            invoice_ocr_obj.page_heights_and_widths,
            add_label_annotations=True,
        )
        doc = fitz.open(f.name)
        alltext = " ".join([page.get_text() for page in doc])
        all_labels = set([i["label"] for i in invoice_predictions])
        for label in all_labels:
            assert label in alltext
