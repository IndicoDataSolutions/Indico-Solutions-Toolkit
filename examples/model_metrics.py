"""
Get extraction field metrics for all Model IDs in a Model Group
"""
from indico_toolkit.metrics import ExtractionMetrics
from indico_toolkit import create_client

MODEL_GROUP_ID = 73
HOST = "app.indico.io"
API_TOKEN_PATH = "./indico_api_token.txt"

client = create_client(HOST, API_TOKEN_PATH)
metrics = ExtractionMetrics(client)
metrics.get_metrics(MODEL_GROUP_ID)

# get a pandas dataframe of field level results
df = metrics.get_metrics_df()
print(df.head())

# get metrics for a specific span type and/or model ID
df = metrics.get_metrics_df(span_type="exact", select_model_id=102)
print(df.head())

# write the results to a CSV (can also optionally pass span_type/model ID here as well)
metrics.to_csv("./my_metrics.pdf")
