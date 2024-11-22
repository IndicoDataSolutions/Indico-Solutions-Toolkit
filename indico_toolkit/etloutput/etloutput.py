import itertools
from bisect import bisect_left, bisect_right
from dataclasses import dataclass
from operator import attrgetter
from typing import TYPE_CHECKING

from .errors import TableCellNotFoundError, TokenNotFoundError
from .table import Table
from .token import Token

if TYPE_CHECKING:
    from collections.abc import Iterable

    from ..results import DocumentExtraction
    from .cell import Cell


@dataclass(frozen=True)
class EtlOutput:
    text: str
    text_on_page: "tuple[str, ...]"

    # Tokens are ordered by span for `token_for` lookup.
    tokens: "tuple[Token, ...]"
    tokens_on_page: "tuple[tuple[Token, ...], ...]"

    # Tables and Cells are ordered by bounding box for `table_cell_for` lookup.
    tables: "tuple[Table, ...]"
    tables_on_page: "tuple[tuple[Table, ...], ...]"

    @staticmethod
    def from_pages(
        text_by_page: "Iterable[str]",
        token_dicts_by_page: "Iterable[Iterable[object]]",
        table_dicts_by_page: "Iterable[Iterable[object]]",
    ) -> "EtlOutput":
        """
        Create an `EtlOutput` from lists of v1 or v3 ETL Ouput dictionaries.
        """
        text_by_page = tuple(text_by_page)
        token_by_page = tuple(
            tuple(map(Token.from_dict, token_dict_page))
            for token_dict_page in token_dicts_by_page
        )
        tables_by_page = tuple(
            tuple(map(Table.from_dict, table_dict_page))
            for table_dict_page in table_dicts_by_page
        )

        return EtlOutput(
            text="\n".join(text_by_page),
            text_on_page=text_by_page,
            tokens=tuple(itertools.chain.from_iterable(token_by_page)),
            tokens_on_page=token_by_page,
            tables=tuple(itertools.chain.from_iterable(tables_by_page)),
            tables_on_page=tables_by_page,
        )

    def token_for(self, extraction: "DocumentExtraction") -> Token:
        """
        Return a `Token` that covers every character from `extraction`.
        Raise `TokenNotFoundError` if one can't be produced.
        """
        try:
            tokens = self.tokens_on_page[extraction.page]
            first = bisect_right(tokens, extraction.start, key=attrgetter("end"))
            last = bisect_left(tokens, extraction.end, lo=first, key=attrgetter("start"))  # fmt: skip # noqa: E501
            tokens = tokens[first:last]

            return Token(
                text=self.text[extraction.start : extraction.end],
                start=extraction.start,
                end=extraction.end,
                page=min(token.page for token in tokens),
                top=min(token.top for token in tokens),
                left=min(token.left for token in tokens),
                right=max(token.right for token in tokens),
                bottom=max(token.bottom for token in tokens),
            )
        except (IndexError, ValueError) as error:
            raise TokenNotFoundError(f"no token contains {extraction!r}") from error

    def table_cell_for(self, token: Token) -> "tuple[Table, Cell]":
        """
        Return the `Table` and `Cell` that contains the midpoint of `token`.
        Raise `NotInTableError` if it's not inside a table.
        """
        token_vmid = (token.top + token.bottom) // 2
        token_hmid = (token.left + token.right) // 2

        for table in self.tables_on_page[token.page]:
            if (table.top <= token_vmid <= table.bottom) and (
                table.left <= token_hmid <= table.right
            ):
                break
        else:
            raise TableCellNotFoundError(f"no table contains {token!r}")

        try:
            row_index = bisect_left(table.rows, token_vmid, key=lambda row: row[0].bottom)  # fmt: skip # noqa: E501
            row = table.rows[row_index]

            cell_index = bisect_left(row, token_hmid, key=attrgetter("right"))
            cell = row[cell_index]
        except (IndexError, ValueError) as error:
            raise TableCellNotFoundError(f"no cell contains {token!r}") from error

        return table, cell
