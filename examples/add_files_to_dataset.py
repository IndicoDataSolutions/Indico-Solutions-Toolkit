"""
Upload files to an existing dataset in batches
"""
from solutions_toolkit.indico_wrapper import Datasets, dataset
from solutions_toolkit.pipelines import FileProcessing
from solutions_toolkit import create_client

DATASET_ID = 1234
HOST = "app.indico.io"
API_TOKEN_PATH = "./indico_api_token.txt"

# Instantiate the datasets class
client = create_client(HOST, API_TOKEN_PATH)
datasets = Datasets(client, DATASET_ID)

# Collect files to upload
fp = FileProcessing()
fp.get_file_paths_from_dir("./datasets/disclosures/")

# Upload files to dataset in batches
for paths in fp.batch_files(batch_size=2):
    datasets.add_to_dataset(paths)
    print(f"Uploaded {len(paths)} files")
