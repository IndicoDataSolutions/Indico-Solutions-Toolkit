import tempfile
from indico_toolkit.snapshots import Snapshot
from indico_toolkit.indico_wrapper import Datasets


# def test_workflow_submit_and_get_rows(indico_client, snapshot_csv_path):
#     snap1 = Snapshot(snapshot_csv_path)
#     snap2 = Snapshot(snapshot_csv_path)
#     snap1.standardize_column_names()
#     snap2.standardize_column_names()
#     snap1.append(snap2)
#     dataset = Datasets(indico_client)
#     with tempfile.NamedTemporaryFile(suffix=".csv") as tf:
#         snap1.to_csv(tf.name)
#         mydataset = dataset.create_dataset([tf.name], "my_dataset")
#         model = dataset.train_model(mydataset, "mymodel", snap1.text_col, snap1.label_col, wait=False)
#         print(f"Model Group ID is {model.id}")
#         assert isinstance(model.id, int)
