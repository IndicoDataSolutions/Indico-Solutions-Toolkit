import os
import pytest
import json

FILE_PATH = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture(scope="session")
def three_row_invoice_preds():
    with open(os.path.join(FILE_PATH, "data/row_association/three_row_invoice/preds.json"), "r") as f:
        preds = json.load(f)
    print(preds)
    return preds


@pytest.fixture(scope="session")
def three_row_invoice_tokens():
    with open(os.path.join(FILE_PATH, "data/row_association/three_row_invoice/tokens.json"), "r") as f:
        tokens = json.load(f)
    return tokens
