from dataclasses import dataclass

from .errors import ResultFileError
from .utils import exists, get


@dataclass
class Span:
    start: int | None
    end: int | None
    page: int

    @staticmethod
    def _from_v1_result(span: object) -> "Span":
        """
        Classify, Extract, and Classify+Extract Workflows.
        """
        try:
            start = get(span, "start", int)
            end = get(span, "end", int)
        except ResultFileError:
            # Post-review extractions may not have start and end keys.
            start = None
            end = None

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
