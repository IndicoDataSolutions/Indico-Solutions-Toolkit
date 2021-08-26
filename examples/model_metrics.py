"""
Get extraction field metrics for all Model IDs in a Model Group
"""
from indico_toolkit.metrics import ExtractionMetrics, CompareModels
from indico_toolkit import create_client

MODEL_GROUP_ID = 73
HOST = "app.indico.io"
API_TOKEN_PATH = "./indico_api_token.txt"

client = create_client(HOST, API_TOKEN_PATH)

"""
Example 1: Explore and compare performance for all models in a Model Group to, for example, see improvement
over time.
"""
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

# get an interactive bar plot to visualize model improvement over time
metrics.bar_plot("./my_bar_plot.html")


"""
Example 2: Compare the performance of two models
"""
# pass the model group and model ID for the two models you want to compare
comp = CompareModels(
    client, model_group_1=6004, model_id_1=33974, model_group_2=6004, model_id_2=33983
)
comp.get_data(span_type="overlap")
print(comp.df.head())

# compare differences for a specific metric
print(comp.get_metric_differences(metric="f1Score"))

# compare the differences in a bar plot
comp.bar_plot(
    "./mycomparison_plot.html",
    plot_title="Difference between labeling strategies",
    bar_colors=["red", "blue"],
)
