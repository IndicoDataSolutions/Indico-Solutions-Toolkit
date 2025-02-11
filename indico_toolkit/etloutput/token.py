from dataclasses import dataclass

from ..results import Box, Span
from ..results.utilities import get


@dataclass(frozen=True)
class Token:
    text: str
    box: Box
    span: Span

    @staticmethod
    def from_dict(token: object) -> "Token":
        """
        Create a `Token` from a v1 or v3 token dictionary.
        """
        get(token, dict, "position")["page_num"] = get(token, int, "page_num")
        get(token, dict, "doc_offset")["page_num"] = get(token, int, "page_num")

        return Token(
            text=get(token, str, "text"),
            box=Box.from_dict(get(token, dict, "position")),
            span=Span.from_dict(get(token, dict, "doc_offset")),
        )
