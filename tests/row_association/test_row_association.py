import json
import pytest
from collections import defaultdict
from indico_toolkit.row_association import Association


def test_grouper_row_number_false_add_to_all(three_row_invoice_preds, three_row_invoice_tokens):
    litems = Association(three_row_invoice_preds, ["work_order_number", "line_date", "work_order_tonnage"])
    litems.get_bounding_boxes(three_row_invoice_tokens)
    litems.assign_row_number()
    assert len(three_row_invoice_preds) - 1 == len(litems._line_item_predictions), "all predictions present in update"
    assert len(litems._non_line_item_predictions) == 1, "non-line item field not ignored"
    assert len(three_row_invoice_preds) == len(litems.updated_predictions.to_list()), "should include all original preds"
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

def test_grouper_no_token_match_raise_exception(three_row_invoice_preds, three_row_invoice_tokens):
    three_row_invoice_tokens.pop()
    litems = Association(three_row_invoice_preds, ["work_order_number", "line_date", "work_order_tonnage"])
    with pytest.raises(Exception):
        litems.get_bounding_boxes(three_row_invoice_tokens)

def test_grouper_no_token_match_no_exception(three_row_invoice_preds, three_row_invoice_tokens):
    three_row_invoice_tokens.pop()
    litems = Association(three_row_invoice_preds, ["work_order_number", "line_date", "work_order_tonnage"])
    litems.get_bounding_boxes(three_row_invoice_tokens, raise_for_no_match=False)
    litems.assign_row_number()
    assert len(litems._errored_predictions) == 1
    assert litems._errored_predictions[0]["error"] == "No matching token found for line item field"
    assert "row_number" not in litems._errored_predictions[0]

def test_get_line_items_in_groups(three_row_invoice_preds, three_row_invoice_tokens):
    litems = Association(
        three_row_invoice_preds,
        ["work_order_number", "line_date", "work_order_tonnage"],
    )
    litems.get_bounding_boxes(three_row_invoice_tokens, raise_for_no_match=False)
    litems.assign_row_number()
    grouped_rows = litems.get_line_items_in_groups()
    assert len(grouped_rows) == 3
    assert isinstance(grouped_rows[0], list)
    assert isinstance(grouped_rows[0][0], dict)

def test_prediction_reordering(three_row_invoice_preds, three_row_invoice_tokens):
    # move the last ordered prediction to the front of the list
    three_row_invoice_preds.insert(0, three_row_invoice_preds.pop())
    litems = Association(
        three_row_invoice_preds,
        ["work_order_number", "line_date", "work_order_tonnage"],
    )
    litems.get_bounding_boxes(three_row_invoice_tokens, raise_for_no_match=False)
    litems.assign_row_number()
    grouped_rows = litems.get_line_items_in_groups()
    assert len(grouped_rows) == 3

def test_empty_line_items_init(three_row_invoice_preds, three_row_invoice_tokens):
    litems = Association(
        three_row_invoice_preds,
    )
    litems.get_bounding_boxes(three_row_invoice_tokens, raise_for_no_match=False)
    litems.assign_row_number()
    grouped_rows = litems.get_line_items_in_groups()
    assert len(grouped_rows) == 3
