from indico_toolkit import create_client
from indico_toolkit.snapshots import Snapshot
from indico_toolkit.indico_wrapper import Datasets

HOST = "app.indico.io"
API_TOKEN_PATH = "./indico_api_token.txt"
PATH_TO_SNAPSHOT = "./snapshot_1.csv"
PATH_TO_SNAPSHOT_2 = "./snapshot_2.csv"
OUTPUT_PATH = "./merged_snapshot_output.csv"

"""
EXAMPLE 1:
Merge the labels from two downloaded teach task snapshots on the same files. 
Example usage: if you labeled different fields for the same documents in separate tasks.
"""
main_snap = Snapshot(PATH_TO_SNAPSHOT)
snap_to_merge = Snapshot(PATH_TO_SNAPSHOT_2)
main_snap.standardize_column_names()
snap_to_merge.standardize_column_names()
main_snap.merge_by_file_name(snap_to_merge, ensure_identical_text=True)
print(main_snap.get_all_labeled_text("Company Name")) # see what text was captured for any label
main_snap.to_csv(OUTPUT_PATH, only_keep_key_columns=True)

"""
EXAMPLE 2:
Combine two identically labeled snapshots together, i.e. stacked on atop the other
Example usage: if you labeled two sets of documents with the same labels in separate teach tasks
"""
main_snap = Snapshot(PATH_TO_SNAPSHOT)
print(main_snap.number_of_samples)
snap_to_append = Snapshot(PATH_TO_SNAPSHOT_2)
main_snap.standardize_column_names()
snap_to_append.standardize_column_names()
main_snap.append(snap_to_append)
print(main_snap.number_of_samples) # will now include all of the samples from snap_to_append as well
main_snap.to_csv(OUTPUT_PATH)

"""
With that merged snapshot, you can now use the toolkit to upload and train a model.
"""
client = create_client(HOST, API_TOKEN_PATH)
dataset = Datasets(client)
uploaded_dataset = dataset.create_dataset([OUTPUT_PATH], dataset_name="my_dataset")
print(f"My Dataset ID is {uploaded_dataset.id}")
model = dataset.train_model(
    uploaded_dataset,
    model_name="my_model",
    source_col=main_snap.text_col,
    target_col=main_snap.label_col,
    wait=False,
)
print(f"My Model Group ID is {model.id}")