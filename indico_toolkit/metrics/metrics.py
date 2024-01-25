import json
import pandas as pd
from typing import List, Dict
from indico import IndicoClient

from indico_toolkit.indico_wrapper import IndicoWrapper
from indico_toolkit import ToolkitInputError
from .plotting import Plotting


class ExtractionMetrics(IndicoWrapper):
    """
    Example usage:

    metrics = ExtractionMetrics(client)
    metrics.get_extraction_metrics(MODEL_GROUP_ID)

    # get a pandas dataframe of field level results
    df = metrics.get_metrics_df()
    print(df.head())

    # get metrics for a specific span type and/or model ID
    df = metrics.get_metrics_df(span_type="exact", select_model_id=102)
    print(df.head())

    # write the results to a CSV (can also optionally pass span_type/model ID here as well)
    metrics.to_csv("./my_metrics.pdf")

    # get an interactive bar plot to visualize model improvement over time
    metrics.bar_plot("./my_bar_plot.html")
    """
    def __init__(self, client: IndicoClient):
        self.client = client
        self.raw_metrics: List[dict] = None
        self.included_models: List[int] = None
        self.number_of_samples: Dict[int, int] = None

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
        self.number_of_samples = {
            model["id"]: int(json.loads(model["modelInfo"])["number_of_examples"])
            for model in self.raw_metrics
        }

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
                scores["number_of_samples"] = self.number_of_samples[model["id"]]
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
        Write an html bar plot to disc to compare model IDs within a model group.
        Will also open the plot automatically in your browser, where you will interactive
        functionality and the ability to download a copy as a PNG as well.

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
        model_ids = sorted(list(df["model_id"].unique()))
        field_order = df.loc[df["model_id"] == model_ids[-1]].sort_values(by=metric)["field_name"].tolist()
        df["field_name"] = df["field_name"].astype("category").cat.set_categories(field_order)
        plotting = Plotting()
        for model_id in model_ids:
            sub_df = df.loc[df["model_id"] == model_id].copy()
            sub_df.sort_values(["field_name"], inplace=True)
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

    def line_plot(
        self,
        output_path: str,
        metric: str = "f1Score",
        span_type: str = "overlap",
        plot_title: str = "",
        ids_to_exclude: List[int] = [],
        fields_to_exclude: List[str] = [],
    ):
        """
        Write an html line plot to disc with # of samples on x-axis, a metric on the y-axis and
        each line representing a distinct field.
        Will also open the plot automatically in your browser, where you will interactive
        functionality and the ability to download a copy as a PNG as well.

        Args:
            output_path (str): where you want to write plot, e.g. "./myplot.html"
            span_type (str): options include 'superset', 'exact', 'overlap' or 'token'
            metric (str, optional): possible values are 'precision', 'recall', 'f1Score', 'falsePositives',
                                    'falseNegatives', 'truePositives'. Defaults to "f1Score".
            plot_title (str, optional): Title of the plot. Defaults to "".
            ids_to_exclude (List[int], optional): Model Ids to exclude from plot.
            fields_to_exclude (List[str], optional): Field Names to exclude from plot.
        """
        df = self.get_metrics_df(span_type=span_type)
        if ids_to_exclude:
            df = df.drop(df.loc[df["model_id"].isin(ids_to_exclude)].index)
        if fields_to_exclude:
            df = df.drop(df.loc[df["field_name"].isin(fields_to_exclude)].index)
        df = df.sort_values(by=["field_name", "number_of_samples", metric])
        plotting = Plotting()
        for field in sorted(df["field_name"].unique()):
            sub_df = df.loc[df["field_name"] == field].copy()
            # ensure only one value per # of samples
            sub_df = sub_df.drop_duplicates(subset=["number_of_samples"])
            plotting.add_line_data(
                sub_df["number_of_samples"],
                sub_df[metric],
                name=field,
                color=None,
            )
        plotting.define_layout(
            xaxis_title="Number of Samples",
            legend_title="Field",
            plot_title=plot_title,
            yaxis_title=metric,
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



class UnbundlingMetrics(ExtractionMetrics):
    """
    Example Usage:

    um = UnbundlingMetrics(client)
    um.get_metrics(1232)
    um.line_plot("./my_metric_plot.html", metric="recall", title="Insurance Model Recall Improvement")

    """
    def get_metrics(self, model_group_id: int):
        """
        Collect all metrics available based on a Model Group ID for an Unbundling model
        Args:
            model_group_id (int): Model Group ID that you're interestd in (available within the Explain UI)
        """
        results = self.graphQL_request(METRIC_QUERY, {"modelGroupId": model_group_id})
        if len(results["modelGroups"]["modelGroups"]) == 0:
            raise ToolkitInputError(
                f"There are no models associated with ID: {model_group_id}"
            )
        results = results["modelGroups"]["modelGroups"][0]["models"]
        raw_metrics = []
        included_models = []
        labeled_samples = []
        for r in results:
            model_info = json.loads(r["modelInfo"])
            if "total_number_of_examples" not in model_info or "metrics" not in model_info:
                # some dictionaries don't come back with required fields... 
                continue
            labeled_samples.append(model_info["total_number_of_examples"])
            included_models.append(r["id"])
            raw_metrics.append(model_info["metrics"]["per_class_metrics"])
        self.raw_metrics = raw_metrics
        self.included_models = included_models
        self.number_of_samples = {model_id:samples for model_id, samples in zip(included_models, labeled_samples)}


    def get_metrics_df(self) -> pd.DataFrame:
        cleaned_metrics = []
        for model_id, metrics in zip(self.included_models, self.raw_metrics):
            for class_name in metrics:
                scores = metrics[class_name]["page"]
                scores["field_name"] = class_name
                scores["model_id"] = model_id
                scores["number_of_samples"] = self.number_of_samples[model_id]
                cleaned_metrics.append(scores)
        df = pd.DataFrame(cleaned_metrics)
        return df.sort_values(by=["field_name", "model_id"], ascending=False)


    def line_plot(
        self,
        output_path: str,
        metric: str = "f1_score",
        plot_title: str = "",
        ids_to_exclude: List[int] = [],
        fields_to_exclude: List[str] = [],
    ):
        """
        Write an html line plot to disc with # of samples on x-axis, a metric on the y-axis and
        each line representing a distinct field.
        Will also open the plot automatically in your browser, where you will interactive
        functionality and the ability to download a copy as a PNG as well.

        Args:
            output_path (str): where you want to write plot, e.g. "./myplot.html"
            span_type (str): options include 'superset', 'exact', 'overlap' or 'token'
            metric (str, optional): possible values are 'precision', 'recall', 'f1_score', 'false_positives',
                                    'false_negatives', 'true_positives'. Defaults to "f1_score".
            plot_title (str, optional): Title of the plot. Defaults to "".
            ids_to_exclude (List[int], optional): Model Ids to exclude from plot.
            fields_to_exclude (List[str], optional): Field Names to exclude from plot.
        """
        df = self.get_metrics_df()
        if ids_to_exclude:
            df = df.drop(df.loc[df["model_id"].isin(ids_to_exclude)].index)
        if fields_to_exclude:
            df = df.drop(df.loc[df["field_name"].isin(fields_to_exclude)].index)
        df = df.sort_values(by=["field_name", "number_of_samples", metric])
        plotting = Plotting()
        for field in sorted(df["field_name"].unique()):
            sub_df = df.loc[df["field_name"] == field].copy()
            # ensure only one value per # of samples
            sub_df = sub_df.drop_duplicates(subset=["number_of_samples"])
            plotting.add_line_data(
                sub_df["number_of_samples"],
                sub_df[metric],
                name=field,
                color=None,
            )
        plotting.define_layout(
            xaxis_title="Number of Samples",
            legend_title="Field",
            plot_title=plot_title,
            yaxis_title=metric,
        )
        plotting.plot(output_path)

    def bar_plot(self):
        raise NotImplementedError("Bar Plot is not currently implemented for unbundling")

    def get_extraction_metrics(self, model_group_id: int):
        raise NotImplementedError("Not available for unbundling class")


METRIC_QUERY = """ 
query modelGroupMetrics($modelGroupId: Int!){
            modelGroups(
                modelGroupIds: [$modelGroupId]
            ) {
                modelGroups {
                    models {
                        id
                        modelInfo
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
