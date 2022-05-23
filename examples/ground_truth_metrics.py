"""
Compare a snapshot containing ground truth to a snapshot containing model predictions
"""
from pydoc import doc
from indico_toolkit.metrics import CompareGroundTruth
import pprint as p

"""
Example 1: GT and MODEL PREDICTIONS FOR A SINGLE DOCUMENT: Say you have the lists of prediction dictionaries for the ground truth
and the model predictions for a single document. Get the metrics for each label as well as metrics for the overall document.
"""

# Replace with your ground truth and model prediction list of dictionaries.
def generate_pred(
    label="Vendor",
    conf_level=0.85,
    start_index=0,
    end_index=2,
    text="Chili's",
):
    return {
        "label": label,
        "text": text,
        "start": start_index,
        "end": end_index,
        "confidence": {label: conf_level},
    }


ground_truth = [
    generate_pred(start_index=0, end_index=11, label="Vendor Name", text="1"),
    generate_pred(start_index=22, end_index=31, label="Vendor Name", text="2"),
    generate_pred(start_index=100, end_index=110, label="Vendor Name", text="3"),
    generate_pred(start_index=10, end_index=21, label="Amount", text="1"),
    generate_pred(start_index=32, end_index=41, label="Amount", text="2"),
    generate_pred(start_index=110, end_index=120, label="Amount", text="3"),
    generate_pred(start_index=10, end_index=15, label="Date", text="1"),
    generate_pred(start_index=16, end_index=20, label="Date", text="2"),
    generate_pred(start_index=110, end_index=120, label="Date", text="3"),
    generate_pred(start_index=10, end_index=35, label="Address", text="1"),
    generate_pred(start_index=500, end_index=520, label="Address", text="2"),
    generate_pred(start_index=600, end_index=620, label="Address", text="3"),
    generate_pred(start_index=10, end_index=35, label="Business Category", text="1"),
    generate_pred(start_index=50, end_index=60, label="Business Category", text="2"),
    generate_pred(start_index=71, end_index=79, label="Business Category", text="3"),
    generate_pred(start_index=10, end_index=35, label="City", text="1"),
    generate_pred(start_index=50, end_index=60, label="City", text="2"),
    generate_pred(start_index=71, end_index=79, label="City", text="3"),
    generate_pred(start_index=10, end_index=35, label="State", text="1"),
    generate_pred(start_index=500, end_index=520, label="State", text="2"),
    generate_pred(start_index=600, end_index=620, label="State", text="3"),
    generate_pred(start_index=100, end_index=106, label="Zip", text="1"),
    generate_pred(start_index=200, end_index=206, label="Zip", text="2"),
    generate_pred(start_index=300, end_index=306, label="Zip", text="3"),
    generate_pred(start_index=400, end_index=406, label="Zip", text="4"),
    generate_pred(start_index=500, end_index=506, label="Zip", text="5"),
    generate_pred(start_index=600, end_index=606, label="Zip", text="6"),
]
predictions = [
    generate_pred(start_index=3, end_index=7, label="Vendor Name", text="A"),
    generate_pred(start_index=32, end_index=41, label="Vendor Name", text="B"),
    generate_pred(start_index=13, end_index=17, label="Amount", text="A"),
    generate_pred(start_index=18, end_index=22, label="Amount", text="B"),
    generate_pred(start_index=42, end_index=51, label="Amount", text="C"),
    generate_pred(start_index=13, end_index=17, label="Date", text="A"),
    generate_pred(start_index=18, end_index=22, label="Date", text="B"),
    generate_pred(start_index=42, end_index=51, label="Date", text="C"),
    generate_pred(start_index=10, end_index=35, label="Address", text="A"),
    generate_pred(start_index=500, end_index=522, label="Address", text="B"),
    generate_pred(start_index=600, end_index=618, label="Address", text="C"),
    generate_pred(start_index=36, end_index=40, label="Business Category", text="A"),
    generate_pred(start_index=61, end_index=70, label="Business Category", text="B"),
    generate_pred(start_index=80, end_index=90, label="Business Category", text="C"),
    generate_pred(start_index=700, end_index=710, label="Business Category", text="D"),
    generate_pred(start_index=36, end_index=40, label="PO Number", text="A"),
    generate_pred(start_index=61, end_index=70, label="PO Number", text="B"),
    generate_pred(start_index=80, end_index=90, label="PO Number", text="C"),
    generate_pred(start_index=700, end_index=710, label="PO Number", text="D"),
    generate_pred(start_index=10, end_index=35, label="State", text="A"),
    generate_pred(start_index=500, end_index=522, label="State", text="B"),
    generate_pred(start_index=100, end_index=106, label="Zip", text="A"),
    generate_pred(start_index=200, end_index=206, label="Zip", text="B"),
    generate_pred(start_index=300, end_index=306, label="Zip", text="C"),
    generate_pred(start_index=400, end_index=406, label="Zip", text="D"),
    generate_pred(start_index=500, end_index=506, label="Zip", text="E"),
    generate_pred(start_index=600, end_index=606, label="Zip", text="F"),
    generate_pred(start_index=700, end_index=706, label="Zip", text="G"),
    generate_pred(start_index=800, end_index=806, label="Zip", text="H"),
    generate_pred(start_index=900, end_index=906, label="Zip", text="H"),
]

# Set the all label metrics and overall metrics for your doc.
cgt_instance = CompareGroundTruth(ground_truth, predictions, "overlap")
cgt_instance.set_all_label_metrics()
cgt_instance.set_overall_metrics()

# Print results
print("All label metrics:")
p.pprint(cgt_instance.all_label_metrics)
print()
print("Overall metrics:")
p.pprint(cgt_instance.overall_metrics)

"""
Example 2: MULTIPLE DOCS FROM SNAPSHOT: Say you have the ground truth and the model predictions for a set of documents in snapshot 
form. From the GT and Model snapshots, loop through each corresponding document's ground truth and model prediction dictionaries 
to get the metrics for each label across all documents as well as metrics for the overall set of documents.
"""
# TODO build out example
