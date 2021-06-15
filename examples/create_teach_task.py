"""
Create a teach task and label it using a csv file
"""
from indico_toolkit.indico_wrapper import Teach
from indico_toolkit import create_client


DATASET_ID = 123
HOST = "app.indico.io"
API_TOKEN_PATH = "./indico_api_token.txt"

# Instantiate the Teach class
client = create_client(HOST, API_TOKEN_PATH)
teach = Teach(client, DATASET_ID)

# Create teach task
teach.create_teach_task("Task Name", ["Class 1", "Class 2"], "Questions")
# Label teach task using snapshot
_ = teach.label_teach_task(
    "./snapshot.csv",
    "question_1620",
    "row_index_6572",
)
print(teach.task.num_fully_labeled)
