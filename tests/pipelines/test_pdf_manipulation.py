import pytest
import tempfile
import fitz
from indico_toolkit.pipelines.pdf_manipulation import ManipulatePDF


@pytest.fixture(scope="function")
def manipulate_pdf_obj(pdf_filepath):
    pdf = ManipulatePDF(pdf_filepath)
    yield pdf
    pdf.close_doc()

def test_page_count(manipulate_pdf_obj):
    assert manipulate_pdf_obj.page_count == 2

@pytest.mark.parametrize("values, num_pages", [([0], 1), ([1], 1), ([0, 1], 2)])
def test_write_subset_of_pages(manipulate_pdf_obj, values, num_pages):
    print(values, num_pages)
    with tempfile.NamedTemporaryFile(suffix=".pdf") as tf:
        text_to_match = manipulate_pdf_obj.get_page_text(min(values))
        manipulate_pdf_obj.write_subset_of_pages(tf.name, values)
        with fitz.open(tf.name) as doc:
            assert doc.pageCount == num_pages
            page_text = doc.get_page_text(0)
            assert page_text == text_to_match
