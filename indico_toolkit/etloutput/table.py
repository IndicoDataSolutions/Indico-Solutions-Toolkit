from dataclasses import dataclass

from .cell import Cell
from .utilities import get


@dataclass(frozen=True)
class Table:
    page: int
    top: int
    left: int
    right: int
    bottom: int

    cells: "tuple[Cell, ...]"
    rows: "tuple[tuple[Cell, ...], ...]"
    columns: "tuple[tuple[Cell, ...], ...]"

    def __lt__(self, other: "Table") -> bool:
        """
        By default, tables are sorted in bounding box order with vertical hysteresis.
        Those on the same line are sorted left-to-right, even when later tables are
        slightly higher than earlier ones.
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
    def from_dict(table: object) -> "Table":
        """
        Create a `Table` from a v1 or v3 table dictionary.
        """
        page = get(table, int, "page_num")
        cells = tuple(
            sorted(Cell.from_dict(cell, page) for cell in get(table, list, "cells"))
        )
        rows = tuple(
            tuple(sorted(cell for cell in cells if row in cell.rows))
            for row in range(get(table, int, "num_rows"))
        )
        columns = tuple(
            tuple(sorted(cell for cell in cells if column in cell.columns))
            for column in range(get(table, int, "num_columns"))
        )

        return Table(
            page=page,
            top=get(table, int, "position", "top"),
            left=get(table, int, "position", "left"),
            right=get(table, int, "position", "right"),
            bottom=get(table, int, "position", "bottom"),
            cells=cells,
            rows=rows,
            columns=columns,
        )
