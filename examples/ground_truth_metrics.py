"""
Compare a snapshot containing ground truth to a snapshot containing model predictions
"""
from pydoc import doc
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
        "label": "Vendor Name",
        "text": "2",
        "start": 22,
        "end": 31,
        "confidence": {"Vendor Name": 0.85},
    },
    {
        "label": "Vendor Name",
        "text": "3",
        "start": 100,
        "end": 110,
        "confidence": {"Vendor Name": 0.85},
    },
    {
        "label": "Amount",
        "text": "1",
        "start": 10,
        "end": 21,
        "confidence": {"Amount": 0.85},
    },
    {
        "label": "Amount",
        "text": "2",
        "start": 32,
        "end": 41,
        "confidence": {"Amount": 0.85},
    },
    {
        "label": "Amount",
        "text": "3",
        "start": 110,
        "end": 120,
        "confidence": {"Amount": 0.85},
    },
    {
        "label": "Date",
        "text": "1",
        "start": 10,
        "end": 15,
        "confidence": {"Date": 0.85},
    },
    {
        "label": "Date",
        "text": "2",
        "start": 16,
        "end": 20,
        "confidence": {"Date": 0.85},
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
        "label": "Vendor Name",
        "text": "B",
        "start": 32,
        "end": 41,
        "confidence": {"Vendor Name": 0.85},
    },
    {
        "label": "Amount",
        "text": "A",
        "start": 13,
        "end": 17,
        "confidence": {"Amount": 0.85},
    },
    {
        "label": "Amount",
        "text": "B",
        "start": 18,
        "end": 22,
        "confidence": {"Amount": 0.85},
    },
    {
        "label": "Amount",
        "text": "C",
        "start": 42,
        "end": 51,
        "confidence": {"Amount": 0.85},
    },
    {
        "label": "Date",
        "text": "A",
        "start": 13,
        "end": 17,
        "confidence": {"Date": 0.85},
    },
    {
        "label": "Date",
        "text": "B",
        "start": 18,
        "end": 22,
        "confidence": {"Date": 0.85},
    },
    {
        "label": "Date",
        "text": "C",
        "start": 42,
        "end": 51,
        "confidence": {"Date": 0.85},
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
Example 2: MULTIPLE DOCS FROM GT SNAPSHOT & MODEL PREDS SNAPSHOT: Say you have the ground truth and the model predictions for a set of documents each in snapshot form. From the GT and Model snapshots, loop through each corresponding document's ground truth and model prediction dictionaries to get the metrics for each label across all documents as well as metrics for the overall set of documents.

Write to disk a merged snapshot with resulting metrics for each document
"""
# Add in your pathways to your ground truth and model pred snapshot csv's
preds_df = pd.read_csv("./example_snapshot_predictions.csv")
gt_df = pd.read_csv("./example_snapshot_groundtruth.csv")

# Create dataframe of the two snapshots, merging on their file name and id
gt_and_preds_df = pd.merge(gt_df, preds_df, on=["file_name", "file_id"])

# Create extra columns for metrics details to be stored for each document
All_Label_Metrics = []
Overall_Label_Metrics = []

# For each document, pull out the ground truth and predictions, instantiate the CGT class, and print out the metrics for each document
for ind in gt_and_preds_df.index:
    ground_truth = eval(gt_and_preds_df["Ground_Truth"][ind])
    preds = eval(gt_and_preds_df["Predictions"][ind])
    cgt_inst = CompareGroundTruth(ground_truth, preds)
    cgt_inst.set_all_label_metrics("overlap")
    cgt_inst.set_overall_metrics()

    All_Label_Metrics.append(cgt_inst.all_label_metrics)
    Overall_Label_Metrics.append(cgt_inst.overall_metrics)

    print("Metrics for doc with file name", gt_and_preds_df["file_name"][ind])
    print(cgt_inst.all_label_metrics)
    print(cgt_inst.overall_metrics)

# Add the by-label and overall metrics to the merged df for reference
gt_and_preds_df["All_Label_Metrics"] = All_Label_Metrics
gt_and_preds_df["Overall_Metrics"] = Overall_Label_Metrics

# Write to csv
gt_and_preds_df.to_csv("./metrics.csv")
