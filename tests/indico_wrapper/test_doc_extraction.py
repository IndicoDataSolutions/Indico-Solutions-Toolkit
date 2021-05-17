from indico_toolkit.ocr import StandardOcr


def test_run_ocr(doc_extraction_wrapper, pdf_filepath):
    extracted_data = doc_extraction_wrapper.run_ocr(filepaths=[pdf_filepath])
    assert len(extracted_data) == 1
    for item in extracted_data:
        assert isinstance(item, StandardOcr)

    extracted_full_text = doc_extraction_wrapper.run_ocr(
        filepaths=[pdf_filepath], text_setting="full_text"
    )
    for item in extracted_full_text:
        assert len(item) == 2062

    extracted_page_texts = doc_extraction_wrapper.run_ocr(
        filepaths=[pdf_filepath], text_setting="page_texts"
    )
    for item in extracted_page_texts:
        assert len(item[0]) == 1153
