from solutions_toolkit.ocr import OnDoc
from solutions_toolkit.ocr import StandardOcr


def test__submit_to_ocr(doc_extraction_wrapper, pdf_filepath):
    jobs = doc_extraction_wrapper._submit_to_ocr(
        preset_config="standard", pdf_filepaths=[pdf_filepath]
    )
    assert len(jobs) == 1


def test_run_ocr(doc_extraction_wrapper, pdf_filepath):
    extracted_data = doc_extraction_wrapper.run_ocr(preset_config="standard", pdf_filepaths=[pdf_filepath])
    assert len(extracted_data) == 1
