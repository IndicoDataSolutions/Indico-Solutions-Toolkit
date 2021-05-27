import os
import json
import pytest


FILE_PATH = os.path.dirname(os.path.abspath(__file__))

@pytest.fixture(scope="function")
def three_row_invoice_preds():
    with open(
        os.path.join(FILE_PATH, "data/three_row_invoice/preds.json"),
        "r",
    ) as f:
        preds = json.load(f)
    return preds


@pytest.fixture(scope="function")
def three_row_invoice_tokens():
    with open(
        os.path.join(FILE_PATH, "data/three_row_invoice/tokens.json"),
        "r",
    ) as f:
        tokens = json.load(f)
    return tokens