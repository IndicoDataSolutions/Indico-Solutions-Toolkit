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
def invoice_pdf_path(highlighter_data_path):
    return os.path.join(highlighter_data_path, "invoice_sample.pdf")


@pytest.fixture(scope="session")
def invoice_ocr_obj(highlighter_data_path):
    return pickle.load(open(os.path.join(highlighter_data_path, "ocr_obj.p"), "rb"))


@pytest.fixture(scope="session")
def invoice_predictions(highlighter_data_path):
    return pickle.load(open(os.path.join(highlighter_data_path, "predictions.p"), "rb"))


@pytest.fixture(scope="session")
def fcc_pdf_path(highlighter_data_path):
    return os.path.join(highlighter_data_path,"fcc_doc.pdf")


@pytest.fixture(scope="session")
def fcc_ocr_obj(highlighter_data_path):
    return pickle.load(open(os.path.join(highlighter_data_path, "fcc_ocr_obj.p"), "rb"))


@pytest.fixture(scope = "session")
def fcc_predictions(highlighter_data_path):
    return pickle.load(open(os.path.join(highlighter_data_path, "fcc_predictions.p"), "rb"))


def test_highlighter_collect_tokens(
    invoice_predictions, invoice_ocr_obj, invoice_pdf_path
):
    highlight = Highlighter(invoice_predictions, invoice_pdf_path)
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
    invoice_predictions, invoice_ocr_obj, invoice_pdf_path
):
    highlight = Highlighter(invoice_predictions, invoice_pdf_path)
    highlight.collect_tokens(invoice_ocr_obj.token_objects)
    number_of_tokens_to_highlight = len(highlight._mapped_positions)
    with tempfile.NamedTemporaryFile(suffix=".pdf") as f:
        highlight.highlight_pdf(f.name, invoice_ocr_obj.page_heights_and_widths)
        doc = fitz.open(f.name)
        num_highlights = sum([1 for page in doc for annotation in page.annots()])
        assert num_highlights == number_of_tokens_to_highlight
        # doc.save("tests/highlighter/data/test_highlighter.pdf")

def test_highlighter_redact_pdf(
    invoice_predictions, invoice_ocr_obj, invoice_pdf_path
):
    highlight = Highlighter(invoice_predictions, invoice_pdf_path)
    highlight.collect_tokens(invoice_ocr_obj.token_objects)
    number_of_tokens_to_redact = len(highlight._mapped_positions)
    with tempfile.NamedTemporaryFile(suffix=".pdf") as f:
        num_redact_annots = highlight.redact_pdf(f.name, invoice_ocr_obj.page_heights_and_widths)
        doc = fitz.open(f.name)
        assert num_redact_annots == number_of_tokens_to_redact
        # doc.save("tests/highlighter/data/test_highlighter_redact.pdf")

def test_highlighter_redact_and_replace_pdf(
    invoice_predictions, invoice_ocr_obj, invoice_pdf_path
):
    highlight = Highlighter(invoice_predictions, invoice_pdf_path)
    highlight.collect_tokens(invoice_ocr_obj.token_objects)
    number_of_tokens_to_redact_and_replace = len(highlight._predictions)
    fill_text = {
        'Invoice Number': 'numerify',
        'Line Item Value': 'pricetag',
        'Line Item': 'text',
        'Total': 'pricetag',
        'Vendor': 'company',
    }
    with tempfile.NamedTemporaryFile(suffix=".pdf") as f:
        num_redact_and_replace_annots = highlight.redact_and_replace(f.name, invoice_ocr_obj.page_heights_and_widths, fill_text)
        doc = fitz.open(f.name)
        assert num_redact_and_replace_annots == number_of_tokens_to_redact_and_replace
        # doc.save("tests/highlighter/data/test_highlighter_redact_and_replace.pdf")

def test_highlighter_bookmarking(
    invoice_predictions, invoice_ocr_obj, invoice_pdf_path
):
    highlight = Highlighter(invoice_predictions, invoice_pdf_path)
    highlight.collect_tokens(invoice_ocr_obj.token_objects)
    with tempfile.NamedTemporaryFile(suffix=".pdf") as f:
        highlight.highlight_pdf(f.name, invoice_ocr_obj.page_heights_and_widths)
        doc = fitz.open(f.name)
        toc = doc.get_toc()
        assert len(toc) == 7
        # 5 first page labels
        assert len([i for i in toc if i[2] == 1]) == 5
        # 2 unique second page labels
        assert len([i for i in toc if i[2] == 2]) == 2

@pytest.mark.parametrize("all_yellow_bool, unique_color_count", [(True, 1), (False, 5)])
def test_highlight_colors(
    invoice_predictions,
    invoice_ocr_obj,
    invoice_pdf_path,
    all_yellow_bool,
    unique_color_count,
):
    highlight = Highlighter(invoice_predictions, invoice_pdf_path)
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
    invoice_pdf_path,
):
    highlight = Highlighter(invoice_predictions, invoice_pdf_path)
    highlight.collect_tokens(invoice_ocr_obj.token_objects)
    with tempfile.NamedTemporaryFile(suffix=".pdf") as f:
        highlight.highlight_pdf(
            f.name,
            invoice_ocr_obj.page_heights_and_widths,
            add_label_annotations=True,
            metadata={"keywords": "Something, Something else"}
        )
        doc = fitz.open(f.name)
        alltext = " ".join([page.get_text() for page in doc])
        all_labels = set([i["label"] for i in invoice_predictions])
        for label in all_labels:
            assert label in alltext
        assert doc.metadata["keywords"] == "Something, Something else"


def test_highlight_two_documents(highlighter_data_path, invoice_predictions, invoice_ocr_obj, invoice_pdf_path, fcc_predictions, fcc_ocr_obj, fcc_pdf_path):
    highlight = Highlighter(invoice_predictions, invoice_pdf_path)
    highlight.collect_tokens(invoice_ocr_obj.token_objects)
    number_of_tokens_to_highlight = len(highlight._mapped_positions)
    with open(os.path.join(highlighter_data_path,"highlighted_invoice.pdf"), 'wb') as f:
        highlight.highlight_pdf(f.name, invoice_ocr_obj.page_heights_and_widths)
        doc = fitz.open(f.name)
        num_highlights = sum([1 for page in doc for annotation in page.annots()])
        assert num_highlights == number_of_tokens_to_highlight


    highlight_2 = Highlighter(fcc_predictions, fcc_pdf_path)
    highlight_2.collect_tokens(fcc_ocr_obj.token_objects)
    number_of_tokens_to_highlight = len(highlight_2._mapped_positions)
    assert any([t not in highlight._mapped_positions for t in highlight_2._mapped_positions])
    with open(os.path.join(highlighter_data_path,"highlighted_fcc.pdf"), 'wb') as f:
        highlight_2.highlight_pdf(f.name, fcc_ocr_obj.page_heights_and_widths)
        doc = fitz.open(f.name)
        num_highlights = sum([1 for page in doc for annotation in page.annots()])
        assert num_highlights == number_of_tokens_to_highlight
