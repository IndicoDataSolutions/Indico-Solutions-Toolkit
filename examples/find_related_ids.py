from indico_toolkit.indico_wrapper import FindRelated
from indico_toolkit import create_client

MODEL_ID = 33318
HOST = "app.indico.io"
API_TOKEN_PATH = "./indico_api_token.txt"

# Instantiate the FindRelated class
client = create_client(HOST, API_TOKEN_PATH)
finder = FindRelated(client)

# Find related 
related = finder.model_id(MODEL_ID)

print(related["workflow_id"])
print(related["dataset_id"])
print(related["selected_model_id"])
print(related["model_group_id"])
print(related["model_name"])
print(related["model_id"])

