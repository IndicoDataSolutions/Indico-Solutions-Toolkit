"""
Get user metrics from the current hosted cluster
Must have admin access to retreive user information
"""
from indico_toolkit.metrics import UserMetrics
from indico_toolkit import create_client

HOST = "app.indico.io"
API_TOKEN_PATH = "./indico_api_token.txt"

client = create_client(HOST, API_TOKEN_PATH)

"""
Example 1: Create a dataframe of user metrics with columns id, name, and email
"""
user_metrics = UserMetrics(client)
df = user_metrics.get_user_metrics_df(columns = ["id", "name", "email"])

"""
Example 2: Write to disk a csv with all availble user metrics columns
"""
#default column is all
user_metrics.to_csv("./my_user_metrics.csv")