"""
Compare a snapshot containing ground truth to a snapshot containing model predictions
"""
from indico_toolkit.metrics import CompareGroundTruth


"""
Example 1: GT and MODEL PREDICTION DICTIONARIES FOR A SINGLE DOCUMENT: Say you have the prediction dictionaries for the ground truth and the model predictions for a single document. Get the metrics for each label as well as metrics for the overall document.
"""

# TODO finish writing up example
ground_truth = {}
predictions = {}

cgt_instance = CompareGroundTruth(ground_truth, predictions)
cgt_instance.get_all_label_metrics_dicts()
cgt_instance.get_overall_label_metrics_dict()

""" 
Example 2: SINGLE DOCUMENT FROM SNAPSHOT: Say you have the ground truth and the model predictions for a single document in snapshot form. From the GT and Model snapshots, get the ground truth and model prediction dictionaries in order to get the metrics for each label as well as metrics for the overall document.
"""

"""
Example 3: MULTIPLE DOCS FROM SNAPSHOT: Say you have the ground truth and the model predictions for a set of documents in snapshot form. From the GT and Model snapshots, loop through each corresponding document's ground truth and model prediction dictionaries to get the metrics for each label across all documents as well as metrics for the overall set of documents.
"""
# TODO would require additional functionality
