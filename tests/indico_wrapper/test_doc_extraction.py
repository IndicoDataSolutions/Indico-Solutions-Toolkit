from indico_toolkit.ocr import StandardOcr


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


def test_run_ocr_custom(doc_extraction_custom, pdf_filepath):
    full_text_result = doc_extraction_custom.run_ocr(
        filepaths=[pdf_filepath], text_setting="full_text"
    )
    assert len(full_text_result[0]) == 2067

    page_texts_result = doc_extraction_custom.run_ocr(
        filepaths=[pdf_filepath], text_setting="page_texts"
    )
    assert len(page_texts_result[0][0]) == 1158
