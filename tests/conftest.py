import os
import pytest
import json
from collections import defaultdict

FILE_PATH = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture(scope="session")
def three_row_invoice_preds():
    with open(os.path.join(FILE_PATH, "data/row_association/three_row_invoice/preds.json"), "r") as f:
        preds = json.load(f)
    return preds


@pytest.fixture(scope="session")
def three_row_invoice_tokens():
    with open(os.path.join(FILE_PATH, "data/row_association/three_row_invoice/tokens.json"), "r") as f:
        tokens = json.load(f)
    return tokens


@pytest.fixture(scope="session")
def auto_review_preds():
    with open(os.path.join(FILE_PATH, "data/auto_review/preds.json"), "r") as f:
        preds = json.load(f)
    return preds


@pytest.fixture(scope="session")
def auto_review_field_config():
    with open(os.path.join(FILE_PATH, "data/auto_review/field_config.json"), "r") as f:
        field_config = json.load(f)
    return field_config


def create_pred_label_map(predictions):
    prediction_label_map = defaultdict(list)
    for pred in predictions:
        label = pred["label"]
        prediction_label_map[label].append(pred)
    return prediction_label_map