"""
Given a dataset of PDFs, write some subset of pages from each PDF to new PDFs
"""
from indico_toolkit.pipelines import FileProcessing, ManipulatePDF

PDF_DIRECTORY = "./path/to/your/pdfs/"
OUTPUT_DIRECTORY = "./path/to/output/pdfs/"
PAGES_TO_KEEP = [0, 1, 4, 8]  # pages you want in your new PDFs

fp = FileProcessing()
fp.get_file_paths_from_dir(path_to_dir=PDF_DIRECTORY, accepted_types=("pdf",))

for pdf_path in fp:
    pdf = ManipulatePDF(pdf_path)
    if pdf.page_count > 8:
        new_pdf_path = fp.join_paths(
            OUTPUT_DIRECTORY, fp.file_name_from_path(pdf_path)
        )
        pdf.write_subset_of_pages(new_pdf_path, PAGES_TO_KEEP)
        pdf.close_doc()
