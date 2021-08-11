import pytest

from indico_toolkit import retry


counter = 0


def test_retry_decor():
    @retry(Exception)
    def no_exceptions():
        return True
    
    @retry((RuntimeError, ConnectionError), num_retries=7)
    def raises_exceptions():
        global counter
        counter +=1
        raise RuntimeError("Test runtime fail")
    
    assert no_exceptions()
    with pytest.raises(RuntimeError):
        raises_exceptions()
    assert counter == 8