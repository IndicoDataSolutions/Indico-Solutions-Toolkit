import pytest


@pytest.fixture(scope="session")
def snapshot_classes():
    snapshot_classes = [
        "Company Name",
        "Stock Symbol",
        "Trader's District",
        "Trader's Name",
        "Transaction Amount",
        "Transaction date",
        "Transaction type",
    ]
    return snapshot_classes
