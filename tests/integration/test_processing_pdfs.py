import pytest
import fitz
from indico_toolkit.pipelines import FileProcessing
from indico_toolkit.pipelines.pdf_manipulation import ManipulatePDF

def test_processing_pdfs(pdf_filepath, tmpdir_factory):
    fp = FileProcessing()
    pdf_dir = fp.get_parent_path(pdf_filepath)
    fp.get_file_paths_from_dir(path_to_dir=pdf_dir, accepted_types=("pdf",))
    assert len([i for i in fp]) == 1
    files_processed = 0
    for pdf_path in fp:
        pdf = ManipulatePDF(pdf_path)
        assert pdf.page_count > 1
        output_path = str(tmpdir_factory.mktemp("data").join(fp.file_name_from_path(pdf_path)))
        pdf.write_subset_of_pages(output_path, [0])
        pdf.close_doc()
        doc = fitz.open(output_path)
        assert doc.pageCount == 1
        files_processed += 1
    assert files_processed == 1
 