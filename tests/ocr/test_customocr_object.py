import pytest
from indico_toolkit.indico_wrapper import DocExtraction


def test_full_text(indico_client, pdf_filepath):
    doc_extraction = DocExtraction(indico_client, preset_config="simple")
    custom_ocr = doc_extraction.run_ocr(filepaths=[pdf_filepath])
    assert len(custom_ocr[0].full_text) == 2823


def test_full_text_exception(indico_client, pdf_filepath):
    doc_extraction = DocExtraction(
        indico_client,
        custom_config={
            "nest": True,
            "top_level": "document",
            "native_pdf": True,
            "blocks": ["text", "position", "doc_offset", "page_offset"],
        },
    )
    custom_ocr = doc_extraction.run_ocr(filepaths=[pdf_filepath])
    with pytest.raises(Exception):
        custom_ocr[0].full_text


def test_page_texts(indico_client, pdf_filepath):
    doc_extraction = DocExtraction(
        indico_client,
        custom_config={
            "nest": True,
            "top_level": "document",
            "native_pdf": True,
            "pages": ["text", "size", "dpi", "doc_offset", "page_num", "image"],
            "blocks": ["text", "position", "doc_offset", "page_offset"],
        },
    )
    custom_ocr = doc_extraction.run_ocr(filepaths=[pdf_filepath])
    assert isinstance(custom_ocr[0].page_texts, list)
    assert isinstance(custom_ocr[0].page_texts[0], str)


def test_page_texts_exception(indico_client, pdf_filepath):
    doc_extraction = DocExtraction(indico_client, preset_config="legacy")
    custom_ocr = doc_extraction.run_ocr(filepaths=[pdf_filepath])
    with pytest.raises(Exception):
        custom_ocr.page_texts
