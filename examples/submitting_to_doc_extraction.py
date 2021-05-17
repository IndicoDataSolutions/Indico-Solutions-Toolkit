from indico_toolkit.indico_wrapper import DocExtraction
from indico_toolkit.pipelines import FileProcessing
from indico_toolkit import create_client

"""
Retrieves a list of raw full document texts for all files in a folder
"""

HOST = "app.indico.io"
API_TOKEN_PATH = "./indico_api_token.txt"

# Instantiate the doc_extraction class
client = create_client(HOST, API_TOKEN_PATH)
doc_extraction = DocExtraction(client=client, preset_config="ondocument")

# Collect files to submit
fp = FileProcessing()
fp.get_file_paths_from_dir("./datasets/disclosures/")

# Submit documents with optional text setting and save results to variable
doc_texts = []
for paths in fp.batch_files(batch_size=10):
    doc_texts.append(doc_extraction.run_ocr(filepaths=paths, text_setting="full_text"))
print(doc_texts)
