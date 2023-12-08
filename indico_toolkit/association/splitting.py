import re
from copy import deepcopy
from itertools import zip_longest
from typing import Any, Dict, Iterator


def split_prediction(
    prediction: Dict[str, Any], separator: str = r"\s*\n\s*"
) -> Iterator[Dict[str, Any]]:
    """
    Split a single `prediction` into mutiple predictions along a `separator` regex
    and yield new predictions having updated text and spans.
    """
    texts_and_delimiters = re.split(f"({separator})", prediction["text"])
    texts = texts_and_delimiters[::2]
    delimiters = texts_and_delimiters[1::2]
    text_and_delimiter_pairs = zip_longest(texts, delimiters)
    start = prediction["start"]
    end = 0

    for text, delimiter in text_and_delimiter_pairs:
        end = start + len(text)

        yield {
            **deepcopy(prediction),
            "text": text,
            "start": start,
            "end": end,
        }

        if delimiter is not None:
            start = end + len(delimiter)
