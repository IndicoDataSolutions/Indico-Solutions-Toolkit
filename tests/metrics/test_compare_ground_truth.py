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


ground_truth_list = [
    generate_pred(
        start_index=100,
        end_index=119,
        label="Zip",
        text="TP exact+overlap",
    ),
    generate_pred(
        start_index=200,
        end_index=219,
        label="Zip",
        text="TP exact+overlap",
    ),
    generate_pred(
        start_index=300,
        end_index=319,
        label="Zip",
        text="TP exact+overlap",
    ),
    generate_pred(
        start_index=400,
        end_index=421,
        label="Zip",
        text="TP overlap, FN+FP exact",
    ),
    generate_pred(
        start_index=500,
        end_index=519,
        label="Zip",
        text="FN exact+overlap",
    ),
    generate_pred(
        start_index=600,
        end_index=619,
        label="Address",
        text="TP exact+overlap",
    ),
    generate_pred(
        start_index=700,
        end_index=719,
        label="Address",
        text="TP exact+overlap",
    ),
]
predictions_list = [
    generate_pred(
        start_index=100,
        end_index=119,
        label="Zip",
        text="TP exact+overlap",
    ),
    generate_pred(
        start_index=200,
        end_index=219,
        label="Zip",
        text="TP exact+overlap",
    ),
    generate_pred(
        start_index=300,
        end_index=319,
        label="Zip",
        text="TP exact+overlap",
    ),
    generate_pred(
        start_index=405,
        end_index=425,
        label="Zip",
        text="TP overlap, FN+FP exact",
    ),
    generate_pred(
        start_index=900,
        end_index=919,
        label="Zip",
        text="FP exact+overlap",
    ),
    generate_pred(
        start_index=600,
        end_index=619,
        label="Address",
        text="TP exact+overlap",
    ),
    generate_pred(
        start_index=700,
        end_index=719,
        label="Address",
        text="TP exact+overlap",
    ),
    generate_pred(
        start_index=800,
        end_index=819,
        label="Address",
        text="FP exact+overlap",
    ),
]


def test_labels():
    cgt_object = CompareGroundTruth(ground_truth_list, predictions_list)
    expected_labels = list(
        set(
            [item["label"] for item in ground_truth_list]
            + [item["label"] for item in predictions_list]
        )
    )
    assert len(expected_labels) == len(cgt_object.labels)
    assert set(expected_labels) == set(cgt_object.labels)


def test_set_all_label_metrics_overlap():
    cgt_object = CompareGroundTruth(ground_truth_list, predictions_list)
    cgt_object.set_all_label_metrics("overlap")
    assert cgt_object.all_label_metrics["Zip"]["true_positives"] == 4
    assert cgt_object.all_label_metrics["Zip"]["false_positives"] == 1
    assert cgt_object.all_label_metrics["Zip"]["false_negatives"] == 1
    assert cgt_object.all_label_metrics["Address"]["true_positives"] == 2
    assert cgt_object.all_label_metrics["Address"]["false_positives"] == 1
    assert cgt_object.all_label_metrics["Address"]["false_negatives"] == 0
    assert len(cgt_object.all_label_metrics) == 2


def test_set_overall_metrics_overlap():
    cgt_object = CompareGroundTruth(ground_truth_list, predictions_list)
    cgt_object.set_all_label_metrics("overlap")
    cgt_object.set_overall_metrics()
    assert len(cgt_object.overall_metrics) == 5
    assert cgt_object.overall_metrics["true_positives"] == 6
    assert cgt_object.overall_metrics["false_positives"] == 2
    assert cgt_object.overall_metrics["false_negatives"] == 1


def test_set_all_label_metrics_exact():
    cgt_object = CompareGroundTruth(ground_truth_list, predictions_list)
    cgt_object.set_all_label_metrics("exact")
    assert cgt_object.all_label_metrics["Zip"]["true_positives"] == 3
    assert cgt_object.all_label_metrics["Zip"]["false_positives"] == 2
    assert cgt_object.all_label_metrics["Zip"]["false_negatives"] == 2
    assert cgt_object.all_label_metrics["Address"]["true_positives"] == 2
    assert cgt_object.all_label_metrics["Address"]["false_positives"] == 1
    assert cgt_object.all_label_metrics["Address"]["false_negatives"] == 0
    assert len(cgt_object.all_label_metrics) == 2


@pytest.mark.parametrize(
    "input_true_p, input_false_p, expected",
    [
        (10, 3, (10 / 13)),
        (0, 0, 0),
        (0, 5, 0),
        (10, 0, 1),
    ],
)
def test_precision(input_true_p, input_false_p, expected):
    cgt_object = CompareGroundTruth(ground_truth_list, predictions_list)
    assert expected == cgt_object._get_precision(input_true_p, input_false_p)


@pytest.mark.parametrize(
    "input_true_p, input_false_n, expected",
    [
        (11, 2, (11 / 13)),
        (0, 0, 0),
        (0, 4, 0),
        (11, 0, 1),
    ],
)
def test_recall(input_true_p, input_false_n, expected):
    cgt_object = CompareGroundTruth(ground_truth_list, predictions_list)
    assert expected == cgt_object._get_recall(input_true_p, input_false_n)
