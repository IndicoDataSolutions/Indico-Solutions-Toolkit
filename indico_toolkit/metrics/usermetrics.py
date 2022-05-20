import pandas as pd
from typing import List
from indico import IndicoClient, IndicoRequestError
from datetime import datetime
from indico_toolkit.errors import (
    ToolkitAuthError,
    ToolkitError,
)
from indico_toolkit.indico_wrapper import IndicoWrapper
from indico.queries.usermetrics import GetUserSnapshots
from indico.filters import UserMetricsFilter
from indico.types.user_metrics import UserSnapshot

USER_METRICS_COLUMNS = [
    "id",
    "name",
    "email",
    "enabled",
    "roles",
    "created_at",
    "datasets",
]


class UserMetrics(IndicoWrapper):
    """
    Class to retrieve users' information on their available cluster.
    User must have app admin access to retrieve this information.
    """

    def __init__(
        self,
        client: IndicoClient,
        datetime: datetime = datetime.now(),
        filter_user_id: int = None,
        filter_email: str = None,
    ):
        """
        filter_user_id(int): ID of a user to filter for
        filter_email(str): Email of a user to filter for
        If user_id and email are not passed, defaults to all available users
        """
        self.client = client
        self.datetime = datetime
        self.filter_user_id = filter_user_id
        self.filter_email = filter_email
        self.df = pd.DataFrame
        self.user_snapshots: List[UserSnapshot] = None

    def get_user_snapshots(
        self,
    )-> None:
        """
        Calls GetUserSnapshots - Requests per-date detailed information about app users.
        Grabs filtered options if passed when initialized.
        Saves list of UserSnapshots to self.
        UserSnapshot:
            id: Unique id tied to user
            name: Name used to sign up
            email: User's email address
            createdAt: Datetime the user was created
            roles: User's roles on the app
            datasets: Datasets accessible to user [dataset_id, user role]
        """
        filter_options = {}
        if self.filter_user_id or self.filter_email:
            filter_options = UserMetricsFilter(
                user_id=self.filter_user_id, user_email=self.filter_email
            )

        try:
            user_snapshots = list(
                self.client.paginate(
                    GetUserSnapshots(date=self.datetime, filters=filter_options)
                )
            )
        except IndicoRequestError:
            ToolkitAuthError(
                "Unauthorized: Please make sure you are an app admin before attempting to retrieve user information"
            )

        if len(user_snapshots) == 0:
            ToolkitError(
                f"Sorry, no user metrics found for id:{self.filter_user_id} or email:{self.filter_email}"
            )

        self.user_snapshots = user_snapshots

    def get_metrics_df(
        self,
    ) -> pd.DataFrame:
        """
        Get a dataframe of user metrics in the caller's cluster from user snapshots.
        """
        if not self.user_snapshots:
            ToolkitError(
                "No user snapshots to turn into a dataframe! Did you run get_user_snapshots first?"
            )

        all_user_metrics = []
        for snapshots in self.user_snapshots:
            for snapshot in snapshots:
                user_metrics = []
                for column in USER_METRICS_COLUMNS:
                    if column == "datasets":
                        datasets = snapshot.datasets
                        users_datasets = [
                            [dataset.dataset_id, dataset.role] for dataset in datasets
                        ]
                        user_metrics.append(users_datasets)
                    else:
                        user_metrics.append(getattr(snapshot, column))

                all_user_metrics.append(user_metrics)

        self.df = pd.DataFrame(all_user_metrics)
        self.df.columns = USER_METRICS_COLUMNS
        return self.df

    def to_csv(
        self,
        output_path: str,
    ) -> None:
        """
        Write a CSV to disc of user metrics from hosted cluster.
        Args:
            output_path (str): path to write CSV on your system, e.g. "./user_metrics.csv"
        """
        self.df.to_csv(output_path, index=False)
