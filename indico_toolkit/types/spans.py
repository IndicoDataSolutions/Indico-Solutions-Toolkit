from dataclasses import dataclass

from .utils import exists, get


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
        if exists(span, "start", int):
            start = get(span, "start", int)
        else:
            # Post-review extractions may not have an start key.
            start = 0

        if exists(span, "end", int):
            end = get(span, "end", int)
        else:
            # Post-review extractions may not have an end key.
            end = 0

        if exists(span, "page_num", int):
            # Pre-review extractions use the page_num key.
            page = get(span, "page_num", int)
        else:
            # Post-review extractions use the pageNum key.
            page = get(span, "pageNum", int)

        return Span(
            start=start,
            end=end,
            page=page,
        )
