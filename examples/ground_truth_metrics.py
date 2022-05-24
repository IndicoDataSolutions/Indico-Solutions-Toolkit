"""
Compare a snapshot containing ground truth to a snapshot containing model predictions
"""
from pydoc import doc
from indico_toolkit.metrics import CompareGroundTruth
import pprint as p

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
p.pprint(cgt_instance.all_label_metrics)
print()
print("Overall metrics:")
p.pprint(cgt_instance.overall_metrics)

"""
Example 2: MULTIPLE DOCS FROM GT SNAPSHOT & MODEL PREDS SNAPSHOT: Say you have the ground truth and the model predictions for a set of documents each in snapshot form. From the GT and Model snapshots, loop through each corresponding document's ground truth and model prediction dictionaries to get the metrics for each label across all documents as well as metrics for the overall set of documents.
"""
# TODO build out example - need to figure out expected format (Would it include spans?)

"""
Example 3: PREDS FROM SUBMISSION RESULT JSON & GT IN SNAPSHOT FORM: 
"""
# TODO build out example - need to figure out expected format
