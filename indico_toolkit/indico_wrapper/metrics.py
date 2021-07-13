import pandas as pd
from typing import List
from indico import IndicoClient

from .indico_wrapper import IndicoWrapper
from indico_toolkit import ToolkitInputError


class ExtractionMetrics(IndicoWrapper):
    def __init__(self, client: IndicoClient):
        self.client = client
        self.raw_metrics: List[dict] = None
        self.included_models: List[int] = None


    def get_metrics(self, model_group_id: int):
        results = self.graphQL_request(METRIC_QUERY, {"modelGroupId": model_group_id})
        if len(results["modelGroups"]["modelGroups"]) == 0:
            raise ToolkitInputError(f"There are no models associated with ID: {model_group_id}")
        results = results["modelGroups"]["modelGroups"][0]["models"]
        self.raw_metrics = [m for m in results if isinstance(m["evaluation"]["metrics"]["classMetrics"], list)]
        self.included_models = [model["id"] for model in self.raw_metrics]


    def get_metrics_df(self, span_type: str = "overlap", select_model_id: int = None) -> pd.DataFrame:
        """
        Get a dataframe of model metrics for a particular span type
        Args:
            span_type (str): options include 'superset', 'exact', 'overlap' or 'token'
            select_model_id (int): only return metrics for a particular model
        """
        if select_model_id :
            if select_model_id not in self.included_models:
                raise ToolkitInputError(f"You must select a model ID from: {self.included_models}")
            model_metrics = [mod for mod in self.raw_metrics if mod["id"] == select_model_id]
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