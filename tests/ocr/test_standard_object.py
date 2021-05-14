from indico_toolkit.ocr import StandardOcr


def test_standard_object_full_text(standard_ocr_object):
    standard_ocr = StandardOcr(standard_ocr_object)
    assert len(standard_ocr.full_text) == 2062


def test_standard_object_page_texts(standard_ocr_object):
    standard_ocr = StandardOcr(standard_ocr_object)
    assert len(standard_ocr.page_texts) == 2
    assert len(standard_ocr.page_texts[0]) == 1153


def test_standard_object_page_results(standard_ocr_object):
    standard_ocr = StandardOcr(standard_ocr_object)
    assert len(standard_ocr.page_results) == 2
    assert len(standard_ocr.page_results[0]) == 4


def test_standard_object_block_texts(standard_ocr_object):
    standard_ocr = StandardOcr(standard_ocr_object)
    assert len(standard_ocr.block_texts) == 36


def test_standard_object_total_pages(standard_ocr_object):
    standard_ocr = StandardOcr(standard_ocr_object)
    assert standard_ocr.total_pages == 2


def test_standard_object_total_characters(standard_ocr_object):
    standard_ocr = StandardOcr(standard_ocr_object)
    assert standard_ocr.total_characters == 2062
