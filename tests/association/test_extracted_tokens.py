import json
import pytest
from collections import defaultdict
from indico_toolkit.association import ExtractedTokens


def test_collect_tokens(three_row_invoice_preds, three_row_invoice_tokens):
    extokens = ExtractedTokens(three_row_invoice_preds)
    extokens.collect_tokens(three_row_invoice_tokens)
    assert len(extokens.extracted_tokens) == 5
    assert len(extokens.predictions) == 6
    assert len(extokens._errored_predictions) == 0
    assert len(extokens._manually_added_preds) == 1
    assert len(extokens._predictions) == 5
    for token in extokens.extracted_tokens:
        assert "label" in token
        assert "text" in token
        assert "page_num" in token


def test_collect_tokens_missing_token_raise_exception(
    three_row_invoice_preds, three_row_invoice_tokens
):
    three_row_invoice_tokens.pop()
    extokens = ExtractedTokens(three_row_invoice_preds)
    with pytest.raises(Exception):
        extokens.collect_tokens(three_row_invoice_tokens)


def test_collect_tokens_missing_token_no_exception(
    three_row_invoice_preds, three_row_invoice_tokens
):
    three_row_invoice_tokens.pop()
    extokens = ExtractedTokens(three_row_invoice_preds)
    extokens.collect_tokens(three_row_invoice_tokens, raise_for_no_match=False)
    assert len(extokens._errored_predictions) == 1
    assert "error" in extokens._errored_predictions[0]


def test_mapped_positions_by_page(three_row_invoice_preds, three_row_invoice_tokens):
    extokens = ExtractedTokens(three_row_invoice_preds)
    extokens.collect_tokens(three_row_invoice_tokens)
    assert isinstance(extokens.mapped_positions_by_page, dict)
    assert len(extokens.mapped_positions_by_page) == 2
    assert len(extokens.mapped_positions_by_page[0]) == 3
    assert len(extokens.mapped_positions_by_page[1]) == 2


def test_prediction_reordering(three_row_invoice_preds, three_row_invoice_tokens):
    # move the last ordered prediction to the front of the list
    three_row_invoice_preds.insert(0, three_row_invoice_preds.pop())
    extokens = ExtractedTokens(three_row_invoice_preds)
    extokens.collect_tokens(three_row_invoice_tokens)
    assert len(extokens.extracted_tokens) == 5


def test_unmmatched_token_skipped(three_row_invoice_preds, three_row_invoice_tokens):
    three_row_invoice_tokens.insert(0, {"doc_offset": {"start": -10, "end": -5}})
    three_row_invoice_tokens.append({"doc_offset": {"start": 1000100, "end": 1000200}})
    extokens = ExtractedTokens(three_row_invoice_preds)
    extokens.collect_tokens(three_row_invoice_tokens)
    assert len(extokens.extracted_tokens) == 5
