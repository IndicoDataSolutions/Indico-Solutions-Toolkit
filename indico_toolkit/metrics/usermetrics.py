import pandas as pd
from typing import List, Dict
from indico import IndicoClient
from datetime import datetime
from indico_toolkit.indico_wrapper import IndicoWrapper
from indico_toolkit import ToolkitInputError
from indico.queries.usermetrics import GetUserSnapshots
from indico.filters import UserMetricsFilter


class UserMetrics(IndicoWrapper):
    def __init__(self, client: IndicoClient):
        self.client = client

    def get_user_metrics_df(
        self,
        columns: List[str] = [
            "id",
            "name",
            "email",
            "enabled",
            "roles",
            "created_at",
            "datasets",
        ],
        date: datetime = datetime.now(),
        filter_user_id: int = None,
        filter_email: str = None,
    ) -> pd.DataFrame:
        """
        Get a dataframe of user metrics in the caller's cluster
        Args:
            columns (List[str]): List of columns to include in the dataframe (OPTIONAL) - defaults to all 
            date (datetime): specific date to query - defaults to current datetime (OPTIONAL)
            filter_user_id (int): user_id to filter for (OPTIONAL)
            filter_email (str): user email to filter for (OPTIONAL)
        """
        filter_opts = {}
        if filter_user_id or filter_email:
            filter_opts = UserMetricsFilter(
                user_id=filter_user_id, filter_email=filter_email
            )

        all_user_metrics = []
        for snapshots in self.client.paginate(
            GetUserSnapshots(date=date, filters=filter_opts)
        ):
            for snapshot in snapshots:
                user_metrics = []
                for column in columns:
                    if column == "datasets":
                        datasets = snapshot.datasets
                        users_datasets = [
                            [dataset.dataset_id, dataset.role] for dataset in datasets
                        ]
                        user_metrics.append(users_datasets)
                    else:
                        user_metrics.append(getattr(snapshot, column))

                all_user_metrics.append(user_metrics)

        df = pd.DataFrame(all_user_metrics)
        df.columns = columns
        return df

    def to_csv(
        self,
        output_path: str,
        columns: List[str] = [
            "id",
            "name",
            "email",
            "enabled",
            "roles",
            "created_at",
            "datasets",
        ],
        date: datetime = datetime.now(),
        filter_user_id: int = None,
        filter_email: str = None,
    ):
        """
        Write a CSV to disc of user metrics from the cluster
        Args:
            output_path (str): path to write CSV on your system, e.g. "./user_metrics.csv"
            columns (List[str]): List of columns to include in the dataframe (OPTIONAL) - defaults to all 
            date (datetime): specific date to query - defaults to current datetime (OPTIONAL)
            filter_user_id (int): user_id to filter for (OPTIONAL)
            filter_email (str): user email to filter for (OPTIONAL)
        """
        df = self.get_user_metrics_df(columns, date, filter_user_id, filter_email)
        df.to_csv(output_path, index=False)
