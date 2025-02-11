from dataclasses import dataclass
from typing import TYPE_CHECKING

from ..utilities import get

if TYPE_CHECKING:
    from typing import Final


@dataclass(frozen=True)
class Box:
    page: int
    top: int
    left: int
    right: int
    bottom: int

    def __lt__(self, other: "Box") -> bool:
        """
        Bounding boxes are sorted with vertical hysteresis. Those on the same line are
        sorted left-to-right, even when later tokens are higher than earlier ones,
        as long as they overlap vertically.

        ┌──────────────────┐ ┌───────────────────┐
        │        1         │ │         2         │
        └──────────────────┘ │                   │
                             └───────────────────┘
                        ┌────────────────┐
        ┌─────────────┐ │        4       │ ┌─────┐
        │      3      │ └────────────────┘ │  5  │
        └─────────────┘                    └─────┘
        """
        return (
            self.page < other.page
            or (self.page == other.page and self.bottom < other.top)
            or (
                self.page == other.page
                and self.top < other.bottom
                and self.left < other.left
            )
        )

    @staticmethod
    def from_dict(box: object) -> "Box":
        return Box(
            page=get(box, int, "page_num"),
            top=get(box, int, "top"),
            left=get(box, int, "left"),
            right=get(box, int, "right"),
            bottom=get(box, int, "bottom"),
        )


# It's more ergonomic to represent the lack of a bounding box with a special null box
# object rather than using `None` or raising an error. This lets you e.g. sort by the
# `box` attribute without having to constantly check for `None`, while still allowing
# you do a "None check" with `extraction.box == NULL_BOX`.
NULL_BOX: "Final" = Box(page=0, top=0, left=0, right=0, bottom=0)
