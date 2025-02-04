from dataclasses import dataclass
from operator import attrgetter

from ..results import Box
from ..results.utilities import get
from .cell import Cell


@dataclass(frozen=True)
class Table:
    box: Box
    cells: "tuple[Cell, ...]"
    rows: "tuple[tuple[Cell, ...], ...]"
    columns: "tuple[tuple[Cell, ...], ...]"

    @staticmethod
    def from_dict(table: object) -> "Table":
        """
        Create a `Table` from a v1 or v3 table dictionary.
        """
        page = get(table, int, "page_num")
        get(table, dict, "position")["page_num"] = page

        cells = tuple(
            sorted(
                (Cell.from_dict(cell, page) for cell in get(table, list, "cells")),
                key=attrgetter("range"),
            )
        )
        rows = tuple(
            tuple(cell for cell in cells if row in cell.range.rows)
            for row in range(get(table, int, "num_rows"))
        )
        columns = tuple(
            tuple(cell for cell in cells if column in cell.range.columns)
            for column in range(get(table, int, "num_columns"))
        )

        return Table(
            box=Box.from_dict(get(table, dict, "position")),
            cells=cells,
            rows=rows,
            columns=columns,
        )
