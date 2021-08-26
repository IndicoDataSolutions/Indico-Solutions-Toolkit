from typing import List, Tuple, Set
from collections import namedtuple
from indico import IndicoClient
import pandas as pd


from .plotting import Plotting
from .metrics import ExtractionMetrics
from indico_toolkit import ToolkitInputError


ModelIds = namedtuple("ModelIds", "group_id id")


class CompareModels(ExtractionMetrics):
    def __init__(
        self,
        client: IndicoClient,
        model_group_1: int,
        model_id_1: int,
        model_group_2: int,
        model_id_2: int,
    ):
        """
        Compare the metrics for two extraction models

        Args:
            client (IndicoClient): instantiated indico client
            model_group_1 (int): model group of first model
            model_id_1 (int): id of first model
            model_group_2 (int): model group of second model
            model_id_2 (int): id of second model
        """
        self.client = client
        self.models = [
            ModelIds(model_group_1, model_id_1),
            ModelIds(model_group_2, model_id_2),
        ]
        self.non_overlapping_fields: Set[str] = None
        self.overlapping_fields: Set[str] = None
        self.df: pd.DataFrame = None

    def get_data(self, span_type: str = "overlap") -> pd.DataFrame:
        """
        Gathers metrics for both models into a dataframe, setting it to self.df
        Args:
            span_type (str): options include 'superset', 'exact', 'overlap' or 'token'
        """
        dfs = []
        for model in self.models:
            metrics = self.get_metrics(model.group_id)
            df = self.get_metrics_df(span_type, model.id)
            df.drop("model_id", axis=1, inplace=True)
            dfs.append(df)
        self._set_labelset_info(dfs)
        if len(self.overlapping_fields) == 0:
            raise ToolkitInputError(
                f"There are no shared labels between the models you provided: {self.non_overlapping_fields}"
            )
        self.df = pd.merge(
            dfs[0], dfs[1], on="field_name", suffixes=self._model_suffixes
        )

    def get_metric_differences(
        self, metric: str = "f1Score", include_difference: bool = True
    ):
        """
        Get a dataframe focused on one metrics, by default sorted by a column of value differences
        Args:
            metric (str, optional): possible values are 'precision', 'recall', 'f1Score', 'falsePositives',
                                    'falseNegatives', 'truePositives'. Defaults to "f1Score".
            include_difference (bool): include a column of the most recent model ID minus the older model ID
        """
        metric_cols = self._get_metric_col_names(metric)
        cols_to_keep = ["field_name", *metric_cols]
        diff_df = self.df[cols_to_keep].copy()
        if include_difference:
            diff_df["difference"] = diff_df[metric_cols[0]] - diff_df[metric_cols[1]]
            diff_df = diff_df.sort_values(by=["difference"], ascending=False)
        return diff_df

    def bar_plot(
        self,
        output_path: str,
        metric: str = "f1Score",
        plot_title: str = "",
        bar_colors: List[str] = ["salmon", "darkblue"],
    ):
        """
        Write an html bar plot to disc. Will also open the plot automatically in your browser, where
        you will interactive functionality and the ability to download a copy as a PNG as well.

        Args:
            output_path (str): where you want to write plot, e.g. "./myplot.html"
            metric (str, optional): possible values are 'precision', 'recall', 'f1Score', 'falsePositives',
                                    'falseNegatives', 'truePositives'. Defaults to "f1Score".
            plot_title (str, optional): Title of the plot. Defaults to "".
            bar_colors (List[str], optional): length two list with the colors for your plot, can be
                                             css color names, rgb, or hex name .
                                             Defaults to ["#EEE8AA", "#98FB98"].
        """
        metric_cols = self._get_metric_col_names(metric, order_descending=False)
        plotting = Plotting()
        for i in range(2):
            plotting.add_barplot_data(
                self.df["field_name"],
                self.df[metric_cols[i]],
                name=self._id_from_col_name(metric_cols[i]),
                color=bar_colors[i],
            )
        plotting.define_layout(
            yaxis_title=metric, legend_title="Model ID", plot_title=plot_title
        )
        plotting.plot(output_path)

    def to_csv(
        self,
        output_path: str,
    ):
        """
        Write a CSV to disc of all model metrics
        Args:
            output_path (str): path to write CSV on your system, e.g. "./my_metrics.csv"
        """
        df.to_csv(output_path, index=False)

    def get_data_df(self):
        raise NotImplementedError(
            "This method is not used by this child class. Use 'df' attribute"
        )

    @staticmethod
    def _id_from_col_name(col_name: str):
        return col_name.split("_")[-1]

    def _get_metric_col_names(self, metric: str, order_descending: bool = True):
        ordered = sorted(
            self._model_suffixes,
            key=lambda x: int(x.replace("_", "")),
            reverse=order_descending,
        )
        return [f"{metric}{suffix}" for suffix in ordered]

    @staticmethod
    def labelsets_overlap(labelset1: set, labelset2: set):
        return labelset1.intersection(labelset2)

    @staticmethod
    def labelset_differences(labelset1: set, labelset2: set):
        return labelset1.symmetric_difference(labelset2)

    @property
    def _model_suffixes(self):
        return f"_{self.models[0].id}", f"_{self.models[1].id}"

    def _set_labelset_info(self, df_list: List[pd.DataFrame]) -> Tuple[set]:
        labelsets = [set(i["field_name"]) for i in df_list]
        self.overlapping_fields = self.labelsets_overlap(labelsets[0], labelsets[1])
        self.non_overlapping_fields = self.labelset_differences(
            labelsets[0], labelsets[1]
        )
