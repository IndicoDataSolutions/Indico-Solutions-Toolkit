import pytest


@pytest.fixture(scope="session")
def snapshot_classes():
    snapshot_classes = [
        "Grand Total Due",
        "Line Cost",
        "Line Description",
        "Quantity",
        "Sub Total",
        "Tax",
        "Transaction Date",
        "Transaction Time",
        "Vendor City",
        "Vendor Name",
        "Vendor State",
        "Vendor Street Address",
        "Vendor Zip Code",
    ]
    return snapshot_classes
