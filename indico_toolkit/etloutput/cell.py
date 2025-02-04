from dataclasses import dataclass
from enum import Enum

from ..results import NULL_SPAN, Box, Span
from ..results.utilities import get
from .range import Range


class CellType(Enum):
    HEADER = "header"
    CONTENT = "content"


@dataclass(frozen=True)
class Cell:
    type: CellType
    text: str
    box: Box
    range: Range
    spans: "tuple[Span, ...]"

    @property
    def span(self) -> Span:
        """
        Return the first `Span` the cell covers or `NULL_SPAN` otherwise.

        Empty cells have no spans.
        """
        return self.spans[0] if self.spans else NULL_SPAN

    @staticmethod
    def from_dict(cell: object, page: int) -> "Cell":
        """
        Create a `Cell` from a v1 or v3 cell dictionary.
        """
        get(cell, dict, "position")["page_num"] = page

        for doc_offset in get(cell, list, "doc_offsets"):
            doc_offset["page_num"] = page

        return Cell(
            type=CellType(get(cell, str, "cell_type")),
            text=get(cell, str, "text"),
            box=Box.from_dict(get(cell, dict, "position")),
            range=Range.from_dict(cell),
            spans=tuple(map(Span.from_dict, get(cell, list, "doc_offsets"))),
        )
