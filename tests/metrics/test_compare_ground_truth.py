import pytest
from indico_toolkit.metrics.compare_ground_truth import CompareGroundTruth


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


"""
EXAMPLE DISTINCTIONS:
TP Variations, All including both FN and FP
    [1] "Vendor Name" Example: 1 GT pred overlaps with 1 model pred (includes both FN and FP)
    [2] "Amount" Example: 1 GT pred overlaps with 2 distinct model preds (includes both FN and FP)
    [3] "Date" Example: 2 distinct GT preds overlap with 1 model pred (includes both FN and FP)
    [4] "Business Category" Example: No true positives (includes both FN and FP)     
Variations where there are only one of each type (TP, FP, FN):
    [5] "Address" Example:  Only true positives; 3 separate GT preds overlap with 3 separate model preds (no FPs or FNs)
    [6] "PO Number" Example: Only false positives; no TPs or FNs
    [7] "City" Example: Only false negatives; no TPs or FPs
Variations where there is 0 for one of each type (TP, FP, FN):
    [8] "State" Example: No false positives
    [9] "Zip" Example: No false negatives
    [4] "Business Category" Example: No true positives (includes both FN and FP)  
"""


ground_truth = {
    "Vendor Name": [
        generate_pred(start_index=0, end_index=11, label="Vendor Name", text="1"),
        generate_pred(start_index=22, end_index=31, label="Vendor Name", text="2"),
        generate_pred(start_index=100, end_index=110, label="Vendor Name", text="3"),
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
        generate_pred(start_index=900, end_index=906, label="Zip", text="H"),
    ],
}
expected_labels = [
    "Address",
    "Amount",
    "Business Category",
    "City",
    "Date",
    "PO Number",
    "State",
    "Vendor Name",
    "Zip",
]
expected_all_label_metrics = {
    "Address": {
        "false_negatives": 0,
        "false_positives": 0,
        "precision": 1.0,
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
        "false_positives": 3,
        "precision": 0.6666666666666666,
        "recall": 1.0,
        "true_positives": 6,
    },
}
expected_overall_label_metrics = {
    "true_positives": 17,
    "false_positives": 14,
    "false_negatives": 12,
    "precision": (17 / (17 + 14)),
    "recall": (17 / (17 + 12)),
}


@pytest.fixture(scope="function")
def CGT_instance():
    cgt_instance = CompareGroundTruth(ground_truth, predictions)
    cgt_instance._get_labels()
    cgt_instance.get_all_label_metrics_dicts()
    cgt_instance.get_overall_label_metrics_dict()
    return cgt_instance


def test_all_label_metrics(CGT_instance):
    assert (
        expected_all_label_metrics["Address"]["false_negatives"]
        == CGT_instance.get_all_label_metrics_dicts()["Address"]["false_negatives"]
    )
    assert (
        expected_all_label_metrics["Zip"]["false_positives"]
        == CGT_instance.get_all_label_metrics_dicts()["Zip"]["false_positives"]
    )
    assert (
        expected_all_label_metrics["Amount"]["true_positives"]
        == CGT_instance.get_all_label_metrics_dicts()["Amount"]["true_positives"]
    )
    assert (
        expected_all_label_metrics["Business Category"]["recall"]
        == CGT_instance.get_all_label_metrics_dicts()["Business Category"]["recall"]
    )
    assert (
        expected_all_label_metrics["PO Number"]["precision"]
        == CGT_instance.get_all_label_metrics_dicts()["PO Number"]["precision"]
    )
    assert expected_all_label_metrics == CGT_instance.get_all_label_metrics_dicts()
    assert len(expected_all_label_metrics) == len(
        CGT_instance.get_all_label_metrics_dicts()
    )


def test_overall_label_metrics(CGT_instance):
    assert (
        CGT_instance.get_overall_label_metrics_dict()["false_negatives"]
        == expected_overall_label_metrics["false_negatives"]
    )
    assert (
        CGT_instance.get_overall_label_metrics_dict()["false_positives"]
        == expected_overall_label_metrics["false_positives"]
    )
    assert (
        CGT_instance.get_overall_label_metrics_dict()["true_positives"]
        == expected_overall_label_metrics["true_positives"]
    )
    assert (
        CGT_instance.get_overall_label_metrics_dict()["recall"]
        == expected_overall_label_metrics["recall"]
    )
    assert (
        CGT_instance.get_overall_label_metrics_dict()["precision"]
        == expected_overall_label_metrics["precision"]
    )
    assert (
        CGT_instance.get_overall_label_metrics_dict() == expected_overall_label_metrics
    )
    assert len(CGT_instance.get_overall_label_metrics_dict()) == len(
        expected_overall_label_metrics
    )


def test_labels(CGT_instance):
    expected_labels.sort()
    labels = CGT_instance._get_labels()
    labels.sort()
    assert len(expected_labels) == len(labels)
    assert expected_labels == labels


def test_precision(CGT_instance):
    assert (10 / 13) == CGT_instance._get_precision(true_p=10, false_p=3)
    assert 0 == CGT_instance._get_precision(true_p=0, false_p=0)


def test_recall(CGT_instance):
    assert (10 / 12) == CGT_instance._get_recall(true_p=10, false_n=2)
    assert 0 == CGT_instance._get_recall(true_p=0, false_n=0)


def test_true_positives(CGT_instance):
    for label in CGT_instance._get_labels():
        assert (
            expected_all_label_metrics[label]["true_positives"]
            == CGT_instance.get_all_label_metrics_dicts()[label]["true_positives"]
        )


def test_false_positives(CGT_instance):
    for label in CGT_instance._get_labels():
        assert (
            expected_all_label_metrics[label]["false_positives"]
            == CGT_instance.get_all_label_metrics_dicts()[label]["false_positives"]
        )


def test_false_negatives(CGT_instance):
    for label in CGT_instance._get_labels():
        assert (
            expected_all_label_metrics[label]["false_negatives"]
            == CGT_instance.get_all_label_metrics_dicts()[label]["false_negatives"]
        )
