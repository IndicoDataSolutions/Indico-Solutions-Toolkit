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

Create a dataset with ReadAPI
ReadAPI is the default OCR option for dataset creation
ocr options can be included as kwargs
ReadAPI kwargs w/ defaults:
    "auto_rotate" (bool): True,
    "single_column" (bool): False,
    "upscale_images" (bool): False,
    "languages" (list): ["ENG"]
"""
dataset_object = datasets.create_dataset(filepaths=fp.file_paths, dataset_name="My ReadAPI dataset", auto_rotate=False, single_column=True)
"""
Example 3:

Create a dataset with Omnipage
ocr options can be included as kwargs
Omnipage kwargs w/ defaults:
    "auto_rotate" (bool): True,
    "single_column" (bool): False,
    "upscale_images" (bool): False,
    "languages" (list): ["ENG"],
    "force_render": True,
    "native_layout": False,
    "native_pdf": False,
    "table_read_order": TableReadOrder.ROW
"""
dataset_object = datasets.create_dataset(filepaths=fp.file_paths, dataset_name="My Omnipage dataset", read_api=False, auto_rotate=False, native_layout=True)
