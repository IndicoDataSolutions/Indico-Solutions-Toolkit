import pytest
from indico_toolkit.metrics.compare_ground_truth import CompareGroundTruth

# TODO find where gen pred func is in toolkit if it already exists // ask Scott if there is a generate pred func that is already in the toolkit and if not, if we should add it
def generate_pred(
    label="Vendor",
    conf_level=0.85,
    start_index=0,
    end_index=2,
    text="Chili's",
    # page_num=None,
    # bbTop=0,
    # dHeight=9,
    # bbLeft=0,
    # dRight=29,
):
    return {
        "label": label,
        "text": text,
        "start": start_index,
        "end": end_index,
        "confidence": {label: conf_level},
        #         "page number": page_num,
        #         "position": {
        #             "bbTop": bbTop,
        #             "bbBot": bbTop + dHeight,
        #             "bbLeft": bbLeft,
        #             "bbRight": bbLeft + dRight,
        #         },
    }


# TODO add in a comment for each test to expalin why they are distinct
# TODO separate out tests to be able to check for different types of failures


def test_compare_ground_truth():
    ground_truth = {
        "Vendor Name": [
            generate_pred(start_index=0, end_index=11, label="Vendor Name", text="1"),
            generate_pred(start_index=22, end_index=31, label="Vendor Name", text="2"),
            generate_pred(
                start_index=100, end_index=110, label="Vendor Name", text="3"
            ),
        ],
        "Amount": [
            generate_pred(start_index=10, end_index=21, label="Amount", text="1"),
            generate_pred(start_index=32, end_index=41, label="Amount", text="2"),
            generate_pred(start_index=110, end_index=120, label="Amount", text="3"),
        ],
        "Date": [
            generate_pred(start_index=10, end_index=15, label="Date", text="1"),
            generate_pred(start_index=16, end_index=20, label="Date", text="2"),
            generate_pred(start_index=110, end_index=120, label="Date", text="3"),
        ],
        "Address": [
            generate_pred(start_index=10, end_index=35, label="Address", text="1"),
            generate_pred(start_index=500, end_index=520, label="Address", text="2"),
            generate_pred(start_index=600, end_index=620, label="Address", text="3"),
        ],
        "Business Category": [
            generate_pred(
                start_index=10, end_index=35, label="Business Category", text="1"
            ),
            generate_pred(
                start_index=50, end_index=60, label="Business Category", text="2"
            ),
            generate_pred(
                start_index=71, end_index=79, label="Business Category", text="3"
            ),
        ],
        "City": [
            generate_pred(start_index=10, end_index=35, label="City", text="1"),
            generate_pred(start_index=50, end_index=60, label="City", text="2"),
            generate_pred(start_index=71, end_index=79, label="City", text="3"),
        ],
        "State": [
            generate_pred(start_index=10, end_index=35, label="State", text="1"),
            generate_pred(start_index=500, end_index=520, label="State", text="2"),
            generate_pred(start_index=600, end_index=620, label="State", text="3"),
        ],
        "Zip": [
            generate_pred(start_index=100, end_index=106, label="Zip", text="1"),
            generate_pred(start_index=200, end_index=206, label="Zip", text="2"),
            generate_pred(start_index=300, end_index=306, label="Zip", text="3"),
            generate_pred(start_index=400, end_index=406, label="Zip", text="4"),
            generate_pred(start_index=500, end_index=506, label="Zip", text="5"),
            generate_pred(start_index=600, end_index=606, label="Zip", text="6"),
        ],
    }
    predictions = {
        "Vendor Name": [
            generate_pred(start_index=3, end_index=7, label="Vendor Name", text="A"),
            generate_pred(start_index=32, end_index=41, label="Vendor Name", text="B"),
        ],
        "Amount": [
            generate_pred(start_index=13, end_index=17, label="Amount", text="A"),
            generate_pred(start_index=18, end_index=22, label="Amount", text="B"),
            generate_pred(start_index=42, end_index=51, label="Amount", text="C"),
        ],
        "Date": [
            generate_pred(start_index=13, end_index=17, label="Date", text="A"),
            generate_pred(start_index=18, end_index=22, label="Date", text="B"),
            generate_pred(start_index=42, end_index=51, label="Date", text="C"),
        ],
        "Address": [
            generate_pred(start_index=10, end_index=35, label="Address", text="A"),
            generate_pred(start_index=500, end_index=522, label="Address", text="B"),
            generate_pred(start_index=600, end_index=618, label="Address", text="C"),
            generate_pred(start_index=700, end_index=710, label="Address", text="D"),
        ],
        "Business Category": [
            generate_pred(
                start_index=36, end_index=40, label="Business Category", text="A"
            ),
            generate_pred(
                start_index=61, end_index=70, label="Business Category", text="B"
            ),
            generate_pred(
                start_index=80, end_index=90, label="Business Category", text="C"
            ),
            generate_pred(
                start_index=700, end_index=710, label="Business Category", text="D"
            ),
        ],
        "PO Number": [
            generate_pred(start_index=36, end_index=40, label="PO Number", text="A"),
            generate_pred(start_index=61, end_index=70, label="PO Number", text="B"),
            generate_pred(start_index=80, end_index=90, label="PO Number", text="C"),
            generate_pred(start_index=700, end_index=710, label="PO Number", text="D"),
        ],
        "State": [
            generate_pred(start_index=10, end_index=35, label="State", text="A"),
            generate_pred(start_index=500, end_index=522, label="State", text="B"),
        ],
        "Zip": [
            generate_pred(start_index=100, end_index=106, label="Zip", text="A"),
            generate_pred(start_index=200, end_index=206, label="Zip", text="B"),
            generate_pred(start_index=300, end_index=306, label="Zip", text="C"),
            generate_pred(start_index=400, end_index=406, label="Zip", text="D"),
            generate_pred(start_index=500, end_index=506, label="Zip", text="E"),
            generate_pred(start_index=600, end_index=606, label="Zip", text="F"),
            generate_pred(start_index=700, end_index=706, label="Zip", text="G"),
            generate_pred(start_index=800, end_index=806, label="Zip", text="H"),
        ],
    }
    expected = {
        "Address": {
            "false_negatives": 0,
            "false_positives": 1,
            "precision": 0.75,
            "recall": 1.0,
            "true_positives": 3,
        },
        "Amount": {
            "false_negatives": 2,
            "false_positives": 1,
            "precision": 0.6666666666666666,
            "recall": 0.5,
            "true_positives": 2,
        },
        "Business Category": {
            "false_negatives": 3,
            "false_positives": 4,
            "precision": 0,
            "recall": 0,
            "true_positives": 0,
        },
        "City": {
            "false_negatives": 3,
            "false_positives": 0,
            "precision": 0,
            "recall": 0,
            "true_positives": 0,
        },
        "Date": {
            "false_negatives": 1,
            "false_positives": 1,
            "precision": 0.75,
            "recall": 0.75,
            "true_positives": 3,
        },
        "PO Number": {
            "false_negatives": 0,
            "false_positives": 4,
            "precision": 0,
            "recall": 0,
            "true_positives": 0,
        },
        "State": {
            "false_negatives": 1,
            "false_positives": 0,
            "precision": 1.0,
            "recall": 0.6666666666666666,
            "true_positives": 2,
        },
        "Vendor Name": {
            "false_negatives": 2,
            "false_positives": 1,
            "precision": 0.5,
            "recall": 0.3333333333333333,
            "true_positives": 1,
        },
        "Zip": {
            "false_negatives": 0,
            "false_positives": 2,
            "precision": 0.75,
            "recall": 1.0,
            "true_positives": 6,
        },
    }
    # TODO Add in more tests - break it out so we can test TP / FN / FP / Recall / Precision separately; we also want to be able to test overall metrics separately
    cgt_instance = CompareGroundTruth(ground_truth, predictions)
    cgt_instance._get_labels()
    cgt_instance._build_metrics_dicts()
    are_metrics_correct = cgt_instance.all_label_metrics
    assert are_metrics_correct == expected
