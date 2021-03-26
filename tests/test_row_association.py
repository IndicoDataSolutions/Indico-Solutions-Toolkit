import json
from collections import defaultdict
from solutions_toolkit.row_association import Association


def test_grouper_row_number_false_add_to_all(three_row_invoice_preds, three_row_invoice_tokens):
    litems = Association(["work_order_number", "line_date", "work_order_tonnage"], three_row_invoice_preds)
    litems.get_bounding_boxes(three_row_invoice_tokens)
    litems.assign_row_number()
    assert len(three_row_invoice_preds) - 1 == len(litems._line_item_predictions), "all predictions present in update"
    assert len(litems._non_line_item_predictions) == 1, "non-line item field not ignored"
    assert len(three_row_invoice_preds) == len(litems.updated_predictions), "should include all original preds"
    assert litems._non_line_item_predictions[0]["label"] == "should be ignored"
    row_count = defaultdict(list)
    for pred in litems._line_item_predictions:
        if "row 1" in pred["text"]:
            assert "row_number" in pred.keys()
            assert pred["row_number"] == 1
            row_count[pred["row_number"]].append(pred["label"])
        elif "row 2" in pred["text"]:
            assert "row_number" in pred.keys()
            assert pred["row_number"] == 2
            row_count[pred["row_number"]].append(pred["label"])
        elif "row 3" in pred["text"]:
            assert "row_number" in pred.keys()
            assert pred["row_number"] == 3
            row_count[pred["row_number"]].append(pred["label"])
    assert 1 in row_count and set(row_count[1]) == set(["line_date", "work_order_tonnage"])
    assert 2 in row_count and set(row_count[2]) == set(["work_order_number"])
    assert 3 in row_count and set(row_count[3]) == set(["work_order_number", "line_date"])
