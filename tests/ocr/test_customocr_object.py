import pytest
from indico_toolkit.indico_wrapper import DocExtraction


def test_customocr_object_full_text(indico_client, pdf_filepath):
    doc_extraction_simple = DocExtraction(indico_client, preset_config="simple")
    custom_ocr_simple = doc_extraction_simple.run_ocr(filepaths=[pdf_filepath])
    assert len(custom_ocr_simple[0].full_text) == 2823

    doc_extraction_custom = DocExtraction(
        indico_client,
        custom_config={
            "nest": True,
            "top_level": "document",
            "native_pdf": True,
            "pages": ["text", "size", "dpi", "doc_offset", "page_num", "image"],
            "blocks": ["text", "position", "doc_offset", "page_offset"],
        },
    )
    custom_ocr = doc_extraction_custom.run_ocr(filepaths=[pdf_filepath])
    with pytest.raises(Exception):
        return custom_ocr.full_text


def test_customocr_object_page_texts(indico_client, pdf_filepath):
    doc_extraction_custom = DocExtraction(
        indico_client,
        custom_config={
            "nest": True,
            "top_level": "document",
            "native_pdf": True,
            "pages": ["text", "size", "dpi", "doc_offset", "page_num", "image"],
            "blocks": ["text", "position", "doc_offset", "page_offset"],
        },
    )
    custom_ocr = doc_extraction_custom.run_ocr(filepaths=[pdf_filepath])
    assert len(custom_ocr[0].page_texts[0]) == 1157

    doc_extraction_legacy = DocExtraction(indico_client, preset_config="legacy")
    custom_ocr_legacy = doc_extraction_legacy.run_ocr(filepaths=[pdf_filepath])
    with pytest.raises(Exception):
        return custom_ocr_legacy.page_texts
