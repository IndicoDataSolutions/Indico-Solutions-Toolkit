from dataclasses import dataclass
from enum import Enum

from .utilities import get, has


class CellType(Enum):
    HEADER = "header"
    CONTENT = "content"


@dataclass(frozen=True)
class Cell:
    type: CellType
    text: str
    # Span
    start: int
    end: int
    # Bounding box
    page: int
    top: int
    left: int
    right: int
    bottom: int
    # Table coordinates
    row: int
    rowspan: int
    rows: "tuple[int, ...]"
    column: int
    columnspan: int
    columns: "tuple[int, ...]"

    def __bool__(self) -> bool:
        """
        A cell is considered empty if its text is empty.
        Supports `if not cell: ...`.
        """
        return bool(self.text)

    def __lt__(self, other: "Cell") -> bool:
        """
        By default, cells are sorted in table order (by row, then column).
        Cells can also be sorted in span order: `tokens.sort(key=attrgetter("start"))`.
        """
        return self.row < other.row or (
            self.row == other.row and self.column < other.column
        )

    @staticmethod
    def from_dict(cell: object, page: int) -> "Cell":
        """
        Create a `Cell` from a v1 or v3 ETL Ouput cell dictionary.
        """
        return Cell(
            type=CellType(get(cell, str, "cell_type")),
            text=get(cell, str, "text"),
            # Empty cells have no start and end; so use [0:0] for a valid slice.
            start=(
                get(cell, int, "doc_offsets", 0, "start")
                if has(cell, dict, "doc_offsets", 0, "start")
                else 0
            ),
            end=(
                get(cell, int, "doc_offsets", 0, "end")
                if has(cell, dict, "doc_offsets", 0, "end")
                else 0
            ),
            page=page,
            top=get(cell, int, "position", "top"),
            left=get(cell, int, "position", "left"),
            right=get(cell, int, "position", "right"),
            bottom=get(cell, int, "position", "bottom"),
            row=get(cell, int, "rows", 0),
            rowspan=len(get(cell, list, "rows")),
            rows=tuple(get(cell, list, "rows")),
            column=get(cell, int, "columns", 0),
            columnspan=len(get(cell, list, "columns")),
            columns=tuple(get(cell, list, "columns")),
        )
