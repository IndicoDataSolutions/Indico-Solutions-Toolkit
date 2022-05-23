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

ground_truth_list = [
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
predictions_list = [
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
expected_overall_metrics = {
    "true_positives": 17,
    "false_positives": 14,
    "false_negatives": 12,
    "precision": (17 / (17 + 14)),
    "recall": (17 / (17 + 12)),
}


@pytest.fixture(scope="function")
def ex_cgt_object():
    cgt_object = CompareGroundTruth(ground_truth_list, predictions_list)
    cgt_object.set_all_label_metrics("overlap")
    cgt_object.set_overall_metrics()
    return cgt_object


def test_labels(ex_cgt_object):
    expected_labels.sort()
    ex_cgt_object.labels.sort()
    assert len(expected_labels) == len(ex_cgt_object.labels)
    assert expected_labels == ex_cgt_object.labels


def test_true_positives(ex_cgt_object):
    for label in ex_cgt_object.labels:
        print(label)
        assert (
            expected_all_label_metrics[label]["true_positives"]
            == ex_cgt_object.all_label_metrics[label]["true_positives"]
        )


def test_false_positives(ex_cgt_object):
    for label in ex_cgt_object.labels:
        assert (
            expected_all_label_metrics[label]["false_positives"]
            == ex_cgt_object.all_label_metrics[label]["false_positives"]
        )


def test_false_negatives(ex_cgt_object):
    for label in ex_cgt_object.labels:
        assert (
            expected_all_label_metrics[label]["false_negatives"]
            == ex_cgt_object.all_label_metrics[label]["false_negatives"]
        )


@pytest.mark.parametrize(
    "input_true_p, input_false_p, expected",
    [
        (10, 3, (10 / 13)),
        (0, 0, 0),
        (0, 5, 0),
        (10, 0, 1),
    ],
)
def test_precision(input_true_p, input_false_p, expected, ex_cgt_object):
    assert expected == ex_cgt_object._get_precision(input_true_p, input_false_p)


@pytest.mark.parametrize(
    "input_true_p, input_false_n, expected",
    [
        (11, 2, (11 / 13)),
        (0, 0, 0),
        (0, 4, 0),
        (11, 0, 1),
    ],
)
def test_recall(ex_cgt_object, input_true_p, input_false_n, expected):
    assert expected == ex_cgt_object._get_recall(input_true_p, input_false_n)


def test_all_label_metrics(ex_cgt_object):
    assert len(expected_all_label_metrics) == len(ex_cgt_object.all_label_metrics)
    assert expected_all_label_metrics == ex_cgt_object.all_label_metrics


def test_overall_label_metrics_true_p(ex_cgt_object):
    assert (
        ex_cgt_object.overall_metrics["true_positives"]
        == expected_overall_metrics["true_positives"]
    )


def test_overall_label_metrics_false_p(ex_cgt_object):
    assert (
        ex_cgt_object.overall_metrics["false_positives"]
        == expected_overall_metrics["false_positives"]
    )


def test_overall_label_metrics_false_n(ex_cgt_object):
    assert (
        ex_cgt_object.overall_metrics["false_negatives"]
        == expected_overall_metrics["false_negatives"]
    )


def test_overall_label_metrics_recall(ex_cgt_object):
    assert ex_cgt_object.overall_metrics["recall"] == expected_overall_metrics["recall"]


def test_overall_label_metrics_precision(ex_cgt_object):
    assert (
        ex_cgt_object.overall_metrics["precision"]
        == expected_overall_metrics["precision"]
    )


def test_overall_label_metrics(ex_cgt_object):
    assert len(ex_cgt_object.overall_metrics) == len(expected_overall_metrics)
    assert ex_cgt_object.overall_metrics == expected_overall_metrics
