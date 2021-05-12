from solutions_toolkit.ocr import OnDoc
from solutions_toolkit.ocr import StandardOcr
from solutions_toolkit.ocr import CustomOcr


def test_run_ocr(doc_extraction_wrapper, pdf_filepath):
    extracted_data = doc_extraction_wrapper.run_ocr(filepaths=[pdf_filepath])
    assert len(extracted_data) == 1
    for item in extracted_data:
        assert isinstance(item, StandardOcr)
