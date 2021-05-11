from indico import IndicoClient

from tests.conftest import API_TOKEN_PATH, HOST_URL, API_TOKEN
from solutions_toolkit.indico_wrapper import DocExtraction
from solutions_toolkit.ocr import OnDoc
from solutions_toolkit.ocr import StandardOcr


def test_doc_extraction_init():
    doc_extraction = DocExtraction(
        HOST_URL,
        api_token_path=API_TOKEN_PATH,
        api_token=API_TOKEN,
    )
    assert isinstance(doc_extraction.indico_client, IndicoClient)


def test_get_extraction_jobs(doc_extraction_wrapper, pdf_filepath):
    jobs = doc_extraction_wrapper.get_extraction_jobs(
        preset_config="standard", pdf_filepaths=[pdf_filepath]
    )
    assert len(jobs) == 1


def test_get_extracted_data(doc_extraction_wrapper, pdf_filepath):
    extracted_data = doc_extraction_wrapper.get_extracted_data(preset_config="standard", pdf_filepaths=[pdf_filepath])
    assert len(extracted_data) == 2


def test_get_ocr_objects(doc_extraction_wrapper, pdf_filepath):
    on_doc = doc_extraction_wrapper.get_ocr_objects(preset_config="ondocument", pdf_filepaths=[pdf_filepath])
    standard_ocr = doc_extraction_wrapper.get_ocr_objects(preset_config="standard", pdf_filepaths=[pdf_filepath])
    assert isinstance(on_doc, OnDoc)
    assert isinstance(standard_ocr, StandardOcr)


def test_get_doc_full_text(doc_extraction_wrapper, pdf_filepath):
    full_text = doc_extraction_wrapper.get_doc_full_text(preset_config="standard", pdf_filepaths=[pdf_filepath])
    assert len(full_text) == 2062


def test_get_doc_page_texts(doc_extraction_wrapper, pdf_filepath):
    page_texts = doc_extraction_wrapper.get_doc_page_texts(preset_config="standard", pdf_filepaths=[pdf_filepath])
    assert len(page_texts) == 2
    assert len(page_texts[0]) == 1153


def test_get_doc_page_results(doc_extraction_wrapper, pdf_filepath):
    page_results = doc_extraction_wrapper.get_doc_page_results(preset_config="standard", pdf_filepaths=[pdf_filepath])
    assert len(page_results) == 2
    assert len(page_results[0]) == 4
