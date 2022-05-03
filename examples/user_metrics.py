"""
Get user metrics from the current hosted cluster
Must have admin access to retreive user information
"""
from datetime import datetime
from indico_toolkit.metrics import UserMetrics
from indico_toolkit import create_client

HOST = "app.indico.io"
API_TOKEN_PATH = "./indico_api_token.txt"

client = create_client(HOST, API_TOKEN_PATH)

"""
Example 1: Instantiate UserMetrics class with date(datetime) and available filters user_id(int) or filter_email(str)
Date defaults to datetime.now if omitted.
If filter_user_id and filter_email are omitted - defaults to all users

"""
user_metrics = UserMetrics(
    client, date=datetime.now(), filter_user_id=100, filter_email="john.doe@email.com"
)

"""
Example 2: Retrieve user snapshots containing user information. Turn snapshot into a dataframe. 
"""
user_metrics.get_user_snapshots()
df = user_metrics.get_metrics_df()

"""
Example 3: Write to disc a csv from dataframe of availble user metrics columns
user metrics columns = [id, name, email, roles, created_at, datasets]
Example of a created csv can be found in ~tests/data/usermetrics
"""
user_metrics.to_csv("../data/user_metrics/my_metrics.csv")
