import os
from indico_toolkit.ocr import StandardOcr
from indico_toolkit.indico_wrapper import DocExtraction
from indico_toolkit import create_client

HOST_URL = os.environ.get("HOST_URL")
API_TOKEN_PATH = os.environ.get("API_TOKEN_PATH")
API_TOKEN = os.environ.get("API_TOKEN")


def test_run_ocr_standard(doc_extraction_standard, pdf_filepath):
    extracted_data = doc_extraction_standard.run_ocr(filepaths=[pdf_filepath])
    assert len(extracted_data) == 1
    for item in extracted_data:
        assert isinstance(item, StandardOcr)

    full_text_result = doc_extraction_standard.run_ocr(
        filepaths=[pdf_filepath], text_setting="full_text"
    )
    assert len(full_text_result[0]) == 2062

    page_texts_result = doc_extraction_standard.run_ocr(
        filepaths=[pdf_filepath], text_setting="page_texts"
    )
    assert len(page_texts_result[0][0]) == 1153


def test_run_ocr_custom(pdf_filepath):
    client = create_client(HOST_URL, API_TOKEN_PATH, API_TOKEN)
    doc_extraction_custom = DocExtraction(client=client, custom_config={
        "top_level": "page",
        "nest": False,
        "reblocking": ["style", "list", "inline-header"],
        "pages": ["text", "size", "dpi", "doc_offset", "page_num", "image", "thumbnail"],
        "blocks": ["text", "doc_offset", "page_offset", "position", "block_type", "page_num"],
        "tokens": ["text", "doc_offset", "page_offset", "block_offset", "position", "page_num", "style"],
        "chars": ["text", "doc_index", "block_index", "page_index", "page_num", "position"]})
    full_text_result = doc_extraction_custom.run_ocr(
        filepaths=[pdf_filepath], text_setting="full_text"
    )
    assert len(full_text_result[0]) == 2067

    page_texts_result = doc_extraction_custom.run_ocr(
        filepaths=[pdf_filepath], text_setting="page_texts"
    )
    assert len(page_texts_result[0][0]) == 1158
