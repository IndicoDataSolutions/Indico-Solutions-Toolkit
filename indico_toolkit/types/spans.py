from dataclasses import dataclass

from .utils import get


@dataclass
class Span:
    start: int
    end: int
    page: int

    @staticmethod
    def _from_v1_result(span: object) -> "Span":
        """
        Classify, Extract, and Classify+Extract Workflows.
        """
        return Span(
            start=get(span, "start", int),
            end=get(span, "end", int),
            page=get(span, "page_num", int),
        )
