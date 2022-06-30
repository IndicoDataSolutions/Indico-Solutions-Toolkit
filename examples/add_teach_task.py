"""
Add a model group to a workflow and train model
"""
from indico_toolkit.indico_wrapper import Workflow, Datasets
from indico_toolkit import create_client

HOST = "app.indico.io"
API_TOKEN_PATH = "./indico_api_token.txt"
PATH_TO_DIR = "./base_directory/"
DATASET_ID = 1234
WORKFLOW_ID = 5678
SOURCE_COL = "text"  # csv column that contained the text
LABEL_COL = "target"  # csv column that contained the labels
# If duplicating a pre-existing model, use all the same values for that model above

# Instantiate the workflow class
client = create_client(HOST, API_TOKEN_PATH)
wflow = Workflow(client)

# If SOURCE_COL and LABEL_COL are unknown, list out
datasets = Datasets
dataset = datasets.get_dataset(DATASET_ID)
[
    print(datacolumn.name) for datacolumn in dataset.datacolumns
]  # source col, typically "text"
[
    print(labelset.name) for labelset in dataset.labelsets
]  # label col, typically "target", or "question_###"

# Advanced model training options
model_training_options = {
    "auto_negative_sampling": False,
    "max_empty_chunk_ratio": 1.0,
}

# Add and train model on worfklow
wflow.add_mg_component(
    model_name="Newly Created Model",
    workflow_id=WORKFLOW_ID,
    dataset_id=DATASET_ID,
    source_col=SOURCE_COL,
    target_col=LABEL_COL,
    model_training_options=model_training_options,
)
