import pytest
from indico_toolkit.ocr import OnDoc


def test_ondoc_full_text(ondoc_ocr_object):
    ondoc_ocr = OnDoc(ondoc_ocr_object)
    assert len(ondoc_ocr.full_text) == 2067


def test_ondoc_page_texts(ondoc_ocr_object):
    ondoc_ocr = OnDoc(ondoc_ocr_object)
    assert len(ondoc_ocr.page_texts) == 2
    assert len(ondoc_ocr.page_texts[0]) == 1158


def test_ondoc_page_results(ondoc_ocr_object):
    ondoc_ocr = OnDoc(ondoc_ocr_object)
    assert len(ondoc_ocr.page_results) == 2
    assert len(ondoc_ocr.page_results[0]) == 8


def test_ondoc_block_texts(ondoc_ocr_object):
    ondoc_ocr = OnDoc(ondoc_ocr_object)
    assert len(ondoc_ocr.block_texts) == 41


def test_ondoc_token_objects(ondoc_ocr_object):
    ondoc_ocr = OnDoc(ondoc_ocr_object)
    assert len(ondoc_ocr.token_objects) == 304


def test_ondoc_total_pages(ondoc_ocr_object):
    ondoc_ocr = OnDoc(ondoc_ocr_object)
    assert ondoc_ocr.total_pages == 2


def test_ondoc_total_characters(ondoc_ocr_object):
    ondoc_ocr = OnDoc(ondoc_ocr_object)
    assert ondoc_ocr.total_characters == 2067


def test_ondoc_total_tokens(ondoc_ocr_object):
    ondoc_ocr = OnDoc(ondoc_ocr_object)
    assert ondoc_ocr.total_tokens == 304


def test_ondoc_confidence(ondoc_ocr_object):
    ondoc_ocr = OnDoc(ondoc_ocr_object)
    assert isinstance(ondoc_ocr.ocr_confidence("mean"), float)
    assert 1 <= ondoc_ocr.ocr_confidence("mean") <= 100


def test_ondoc_confidence_metric_exception(ondoc_ocr_object):
    ondoc_ocr = OnDoc(ondoc_ocr_object)
    with pytest.raises(Exception):
        ondoc_ocr.ocr_confidence("average")


def test_ondoc_excluded_confidence_exception(ondoc_ocr_object):
    ondoc_ocr = OnDoc(ondoc_ocr_object[0]["chars"][0].pop("confidence"))
    with pytest.raises(Exception):
        ondoc_ocr.ocr_confidence("mean")
