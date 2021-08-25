import pandas as pd
from typing import List
from indico import IndicoClient

from indico_toolkit.indico_wrapper import IndicoWrapper
from indico_toolkit import ToolkitInputError
from .plotting import Plotting


class ExtractionMetrics(IndicoWrapper):
    def __init__(self, client: IndicoClient):
        self.client = client
        self.raw_metrics: List[dict] = None
        self.included_models: List[int] = None

    def get_metrics(self, model_group_id: int):
        results = self.graphQL_request(METRIC_QUERY, {"modelGroupId": model_group_id})
        if len(results["modelGroups"]["modelGroups"]) == 0:
            raise ToolkitInputError(
                f"There are no models associated with ID: {model_group_id}"
            )
        results = results["modelGroups"]["modelGroups"][0]["models"]
        self.raw_metrics = [
            m
            for m in results
            if isinstance(m["evaluation"]["metrics"]["classMetrics"], list)
        ]
        self.included_models = [model["id"] for model in self.raw_metrics]

    def get_metrics_df(
        self, span_type: str = "overlap", select_model_id: int = None
    ) -> pd.DataFrame:
        """
        Get a dataframe of model metrics for a particular span type
        Args:
            span_type (str): options include 'superset', 'exact', 'overlap' or 'token'
            select_model_id (int): only return metrics for a particular model
        """
        if select_model_id:
            if select_model_id not in self.included_models:
                raise ToolkitInputError(
                    f"You must select a model ID from: {self.included_models}"
                )
            model_metrics = [
                mod for mod in self.raw_metrics if mod["id"] == select_model_id
            ]
        else:
            model_metrics = self.raw_metrics
        cleaned_metrics = []
        for model in model_metrics:
            class_metrics = model["evaluation"]["metrics"]["classMetrics"]
            for metric in class_metrics:
                scores = [i for i in metric["metrics"] if i["spanType"] == span_type][0]
                scores["field_name"] = metric["name"]
                scores["model_id"] = model["id"]
                cleaned_metrics.append(scores)
        df = pd.DataFrame(cleaned_metrics)
        return df.sort_values(by=["field_name", "model_id"], ascending=False)

    def bar_plot(
        self,
        output_path: str,
        metric: str = "f1Score",
        span_type: str = "overlap",
        plot_title: str = "",
        ids_to_exclude: List[int] = [],
    ):
        """
        Write an html bar plot to disc. Will also open the plot automatically in your browser, where
        you will interactive functionality and the ability to download a copy as a PNG as well.

        Args:
            output_path (str): where you want to write plot, e.g. "./myplot.html"
            span_type (str): options include 'superset', 'exact', 'overlap' or 'token'
            metric (str, optional): possible values are 'precision', 'recall', 'f1Score', 'falsePositives',
                                    'falseNegatives', 'truePositives'. Defaults to "f1Score".
            plot_title (str, optional): Title of the plot. Defaults to "".
            ids_to_exclude (List[int], optional): Model Ids to exclude from plot.
        """
        df = self.get_metrics_df(span_type=span_type)
        if ids_to_exclude:
            df = df.drop(df.loc[df["model_id"].isin(ids_to_exclude)].index)

        plotting = Plotting()
        for model_id in sorted(df["model_id"].unique()):
            sub_df = df.loc[df["model_id"] == model_id]
            plotting.add_barplot_data(
                sub_df["field_name"],
                sub_df[metric],
                name=str(model_id),
                color=None,
            )
        plotting.define_layout(
            yaxis_title=metric, legend_title="Model ID", plot_title=plot_title
        )
        plotting.plot(output_path)

    def to_csv(
        self, output_path: str, span_type: str = "overlap", select_model_id: int = None
    ):
        """
        Write a CSV to disc of model metrics for a particular span type and/or model ID
        Args:
            output_path (str): path to write CSV on your system, e.g. "./my_metrics.csv"
            span_type (str): options include 'superset', 'exact', 'overlap' or 'token'
            select_model_id (int): only return metrics for a particular model (OPTIONAL)
        """
        df = self.get_metrics_df(span_type, select_model_id)
        df.to_csv(output_path, index=False)


METRIC_QUERY = """ 
query modelGroupMetrics($modelGroupId: Int!){
            modelGroups(
                modelGroupIds: [$modelGroupId]
            ) {
                modelGroups {
                    models {
                        id
                        evaluation {
                        ... on AnnotationEvaluation {
                            metrics {
                                classMetrics {
                                    name
                                    metrics {
                                        spanType
                                        precision
                                        recall
                                        f1Score
                                        falsePositives
                                        falseNegatives
                                        truePositives
                                    }
                                }
                                retrainForMetrics
                            }
                        }
                    }
                }
            }
        }
    }
"""
