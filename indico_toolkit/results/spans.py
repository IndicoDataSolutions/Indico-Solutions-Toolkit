from dataclasses import dataclass

from .errors import ResultFileError
from .utils import exists, get


@dataclass
class Span:
    start: "int | None"
    end: "int | None"
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
            page = get(span, "page_num", int)
        else:
            # A platform bug causes manual-review extractions to use a different key.
            page = get(span, "pageNum", int)

        return Span(
            start=start,
            end=end,
            page=page,
        )

    @staticmethod
    def _from_v2_result(span: object) -> "Span":
        """
        Bundled Submission Workflows.
        """
        return Span(
            start=get(span, "start", int),
            end=get(span, "end", int),
            page=get(span, "page_num", int),
        )

    @classmethod
    def _from_v3_result(cls, span: object) -> "Span":
        """
        Classify+Unbundle Workflows.
        """
        return cls._from_v2_result(span)
