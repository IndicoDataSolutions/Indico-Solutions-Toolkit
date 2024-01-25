from indico_toolkit import create_client
from indico_toolkit.auto_populate import AutoPopulator

"""
Create a new copied Workflow based on given Teach Task Id 
and corresponding Dataset Id.
"""

HOST = "app.indico.io"
API_TOKEN_PATH = "./indico_api_token.txt"
DATASET_ID = 0
TEACH_TASK_ID = 0

client = create_client(HOST, API_TOKEN_PATH)
auto_populator = AutoPopulator(client)
new_workflow = auto_populator.copy_teach_task(
    dataset_id=DATASET_ID,
    teach_task_id=TEACH_TASK_ID,
    workflow_name=f"Copied Workflow",
)
