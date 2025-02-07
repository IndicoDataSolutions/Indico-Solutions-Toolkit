from dataclasses import dataclass
from typing import TYPE_CHECKING

from ..utilities import get

if TYPE_CHECKING:
    from typing import Any, Final


@dataclass(order=True, frozen=True)
class Span:
    page: int
    start: int
    end: int

    @property
    def slice(self) -> slice:
        return slice(self.start, self.end)

    def __bool__(self) -> bool:
        return self != NULL_SPAN

    @staticmethod
    def from_dict(span: object) -> "Span":
        return Span(
            page=get(span, int, "page_num"),
            start=get(span, int, "start"),
            end=get(span, int, "end"),
        )

    def to_dict(self) -> "dict[str, Any]":
        return {
            "page_num": self.page,
            "start": self.start,
            "end": self.end,
        }


# It's more ergonomic to represent the lack of spans with a special null span object
# rather than using `None` or raising an error. This lets you e.g. sort by the `span`
# attribute without having to constantly check for `None`, while still allowing you do
# a "None check" with `extraction.span == NULL_SPAN` or `bool(extraction.span)`.
NULL_SPAN: "Final" = Span(page=0, start=0, end=0)
