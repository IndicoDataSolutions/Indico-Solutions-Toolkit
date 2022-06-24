"""
Compare a snapshot containing ground truth to a snapshot containing model predictions
"""
import pandas as pd

from indico_toolkit.metrics import CompareGroundTruth

"""
Example 1: GT and MODEL PREDICTIONS LISTS FOR A SINGLE DOCUMENT: Say you have the lists of prediction dictionaries for the ground truth
and the model predictions for a single document. Get the metrics for each label as well as metrics for the overall document.
"""

# Replace with your ground truth and model prediction list of dictionaries.
ground_truth = [
    {
        "label": "Vendor Name",
        "text": "1",
        "start": 0,
        "end": 11,
        "confidence": {"Vendor Name": 0.85},
    },
    {
        "label": "Amount",
        "text": "1",
        "start": 10,
        "end": 21,
        "confidence": {"Amount": 0.85},
    },
]
predictions = [
    {
        "label": "Vendor Name",
        "text": "A",
        "start": 3,
        "end": 7,
        "confidence": {"Vendor Name": 0.85},
    },
    {
        "label": "Amount",
        "text": "A",
        "start": 13,
        "end": 17,
        "confidence": {"Amount": 0.85},
    },
]

# Set the all label metrics and overall metrics for your doc.
cgt_instance = CompareGroundTruth(ground_truth, predictions)
cgt_instance.set_all_label_metrics("overlap")
cgt_instance.set_overall_metrics()

# Print results
print("All label metrics:")
print(cgt_instance.all_label_metrics)
print("Overall metrics:")
print(cgt_instance.overall_metrics)

"""
Example 2: MULTIPLE DOCS FROM GT SNAPSHOT & MODEL PREDS SNAPSHOT: Say you have the ground truth and the model predictions for a set of documents in snapshot form. Write to disk a merged snapshot with resulting metrics for each document.
"""
# Add in your pathways to your ground truth and model pred snapshot csv's
preds_df = pd.read_csv("./example_snapshot_predictions.csv")
gt_df = pd.read_csv("./example_snapshot_groundtruth.csv")

# Create dataframe of the two snapshots, merging on their file name and id
gt_and_preds_df = pd.merge(gt_df, preds_df, on=["file_name", "file_id"])

# Create extra columns for metrics details to be stored for each document
all_label_metrics_lst = []
overall_label_metrics_lst = []

# For each document, pull out the ground truth and predictions, instantiate the CGT class, and print out the metrics for each document
for ind in gt_and_preds_df.index:
    ground_truth = eval(gt_and_preds_df["Ground_Truth"][ind])
    preds = eval(gt_and_preds_df["Predictions"][ind])
    cgt_inst = CompareGroundTruth(ground_truth, preds)
    cgt_inst.set_all_label_metrics("overlap")
    cgt_inst.set_overall_metrics()

    all_label_metrics_lst.append(cgt_inst.all_label_metrics)
    overall_label_metrics_lst.append(cgt_inst.overall_metrics)

    print("Metrics for doc with file name", gt_and_preds_df["file_name"][ind])
    print(cgt_inst.all_label_metrics)
    print(cgt_inst.overall_metrics)

# Add the by-label and overall metrics to the merged df for reference
gt_and_preds_df["All_Label_Metrics"] = all_label_metrics_lst
gt_and_preds_df["Overall_Metrics"] = overall_label_metrics_lst

# Write to csv
gt_and_preds_df.to_csv("./metrics.csv")
