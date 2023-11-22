from indico_toolkit import create_client
from indico_toolkit.indico_wrapper.download import Download

HOST = "app.indico.io"
API_TOKEN_PATH = "./indico_api_token.txt"
DATASET_ID = 000
LABELSET_ID = 000 
SUBMISSION_ID = 000

client = create_client(HOST, API_TOKEN_PATH)
downloader = Download(client)

"""
EXAMPLE 1:
Download PDFs from an uploaded dataset to a local directory
"""

downloader.get_dataset_pdfs(dataset_id=DATASET_ID, labelset_id=LABELSET_ID, output_dir="./data/downloads/")

"""
EXAMPLE 2:
Downloads source pdf from a submission id and writes to disk.
"""

downloader.get_submission_pdf(submission_id=SUBMISSION_ID, output_dir="./data/downloads/")


