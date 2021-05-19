from indico_toolkit.ocr import StandardOcr, OnDoc
from indico_toolkit.indico_wrapper import DocExtraction


def test_run_ocr_ondoc(indico_client, pdf_filepath):
    doc_extraction_ondoc = DocExtraction(indico_client, preset_config="ondocument")
    extracted_data = doc_extraction_ondoc.run_ocr(filepaths=[pdf_filepath])
    for item in extracted_data:
        assert isinstance(item, OnDoc)


def test_run_ocr_standard(doc_extraction_standard, pdf_filepath):
    extracted_data = doc_extraction_standard.run_ocr(filepaths=[pdf_filepath])
    for item in extracted_data:
        assert isinstance(item, StandardOcr)


def test_run_ocr_standard_full_text(doc_extraction_standard, pdf_filepath):
    full_text_result = doc_extraction_standard.run_ocr(
        filepaths=[pdf_filepath], text_setting="full_text"
    )
    assert len(full_text_result[0]) == 2062


def test_run_ocr_standard_page_texts(doc_extraction_standard, pdf_filepath):
    page_texts_result = doc_extraction_standard.run_ocr(
        filepaths=[pdf_filepath], text_setting="page_texts"
    )
    assert len(page_texts_result[0][0]) == 1153


def test_run_ocr_custom_full_text(indico_client, pdf_filepath):
    doc_extraction_custom = DocExtraction(indico_client, custom_config={
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


def test_run_ocr_custom_page_texts(indico_client, pdf_filepath):
    doc_extraction_custom = DocExtraction(indico_client, custom_config={
        "top_level": "page",
        "nest": False,
        "reblocking": ["style", "list", "inline-header"],
        "pages": ["text", "size", "dpi", "doc_offset", "page_num", "image", "thumbnail"],
        "blocks": ["text", "doc_offset", "page_offset", "position", "block_type", "page_num"],
        "tokens": ["text", "doc_offset", "page_offset", "block_offset", "position", "page_num", "style"],
        "chars": ["text", "doc_index", "block_index", "page_index", "page_num", "position"]})
    page_texts_result = doc_extraction_custom.run_ocr(
        filepaths=[pdf_filepath], text_setting="page_texts"
    )
    assert len(page_texts_result[0][0]) == 1158
