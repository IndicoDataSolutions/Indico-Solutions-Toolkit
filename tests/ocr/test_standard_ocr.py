from solutions_toolkit.ocr import Standard


def test_standard_ocr_object(standard_ocr_object):
    standard_ocr = Standard(standard_ocr_object)
    assert isinstance(standard_ocr, Standard)
    assert standard_ocr.total_pages == 8
