from dataclasses import dataclass

from ..results.utilities import get


@dataclass(order=True, frozen=True)
class Range:
    row: int
    column: int
    rowspan: int
    columnspan: int
    rows: "tuple[int, ...]"
    columns: "tuple[int, ...]"

    @staticmethod
    def from_dict(cell: object) -> "Range":
        """
        Create a `Range` from a v1 or v3 cell dictionary.
        """
        rows = get(cell, list, "rows")
        columns = get(cell, list, "columns")

        return Range(
            row=rows[0],
            column=columns[0],
            rowspan=len(rows),
            columnspan=len(columns),
            rows=tuple(rows),
            columns=tuple(columns),
        )
