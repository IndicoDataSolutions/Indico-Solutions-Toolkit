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
"""
Example 2:

Create a dataset and then download it
"""
# Create a dataset and return a dataset object
dataset_object = datasets.create_dataset(filepaths=fp.file_paths, dataset_name="My dataset")
# Export is returned as a pandas DataFrame
df = downloader.get_dataset_dataframe(dataset_id=dataset_object.id, labelset_id=dataset_object.labelsets[0].id)
# view first 5 rows of the dataset as a CSV
print(df.head())
# Write to downloaded dataset to CSV
df.to_csv("./mydataset.csv")
