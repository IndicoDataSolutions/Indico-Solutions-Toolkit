from indico_toolkit.indico_wrapper import Datasets, Download
from indico_toolkit.pipelines import FileProcessing
from indico_toolkit import create_client

DATASET_ID = 1234
HOST = "app.indico.io"
API_TOKEN_PATH = "./indico_api_token.txt"

# Instantiate the datasets class
client = create_client(HOST, API_TOKEN_PATH)
datasets = Datasets(client, DATASET_ID)
downloader = Download(client)
"""
Example 1:

Upload files to an existing dataset in batches
"""
# Collect files to upload
fp = FileProcessing()
fp.get_file_paths_from_dir("./datasets/disclosures/")

# Upload files to dataset in batches
for paths in fp.batch_files(batch_size=2):
    datasets.add_files_to_dataset(paths)
    print(f"Uploaded {len(paths)} files")

