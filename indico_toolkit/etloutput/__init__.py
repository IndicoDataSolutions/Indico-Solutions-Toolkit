from typing import TYPE_CHECKING

from ..results.utilities import get, has
from .cell import Cell, CellType
from .errors import EtlOutputError, TableCellNotFoundError, TokenNotFoundError
from .etloutput import EtlOutput
from .table import Table
from .token import Token

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable
    from typing import Any

__all__ = (
    "Cell",
    "CellType",
    "EtlOutput",
    "EtlOutputError",
    "load",
    "load_async",
    "Table",
    "TableCellNotFoundError",
    "Token",
    "TokenNotFoundError",
)


def load(
    etl_output_uri: str,
    *,
    reader: "Callable[..., Any]",
    text: bool = True,
    tokens: bool = True,
    tables: bool = False,
) -> EtlOutput:
    """
    Load `etl_output_uri` as an ETL Output dataclass. A `reader` function must be
    supplied to read JSON files from disk, storage API, or Indico client.

    Use `text`, `tokens`, and `tables` to specify what to load.

    ```
    result = results.load(submission.result_file, reader=read_uri)
    etl_outputs = {
        document: etloutput.load(document.etl_output_uri, reader=read_uri)
        for document in result.documents
    }
    ```
    """
    etl_output = reader(etl_output_uri)
    tables_uri = etl_output_uri.replace("etl_output.json", "tables.json")

    if has(etl_output, str, "pages", 0, "page_info"):
        return _load_v1(etl_output, tables_uri, reader, text, tokens, tables)
    else:
        return _load_v3(etl_output, tables_uri, reader, text, tokens, tables)


async def load_async(
    etl_output_uri: str,
    *,
    reader: "Callable[..., Awaitable[Any]]",
    text: bool = True,
    tokens: bool = True,
    tables: bool = False,
) -> EtlOutput:
    """
    Load `etl_output_uri` as an ETL Output dataclass. A `reader` coroutine must be
    supplied to read JSON files from disk, storage API, or Indico client.

    Use `text`, `tokens`, and `tables` to specify what to load.

    ```
    result = await results.load_async(submission.result_file, reader=read_uri)
    etl_outputs = {
        document: await etloutput.load_async(document.etl_output_uri, reader=read_uri)
        for document in result.documents
    }
    ```
    """
    etl_output = await reader(etl_output_uri)
    tables_uri = etl_output_uri.replace("etl_output.json", "tables.json")

    if has(etl_output, str, "pages", 0, "page_info"):
        return await _load_v1_async(
            etl_output, tables_uri, reader, text, tokens, tables
        )
    else:
        return await _load_v3_async(
            etl_output, tables_uri, reader, text, tokens, tables
        )


def _load_v1(
    etl_output: "Any",
    tables_uri: str,
    reader: "Callable[..., Any]",
    text: bool,
    tokens: bool,
    tables: bool,
) -> EtlOutput:
    if text or tokens:
        pages = tuple(
            reader(get(page, str, "page_info"))
            for page in get(etl_output, list, "pages")
        )
        text_by_page = map(lambda page: get(page, str, "pages", 0, "text"), pages)
        tokens_by_page = map(lambda page: get(page, list, "tokens"), pages)
    else:
        text_by_page = ()  # type: ignore[assignment]
        tokens_by_page = ()  # type: ignore[assignment]

    if tables:
        tables_by_page = reader(tables_uri)
    else:
        tables_by_page = ()

    return EtlOutput.from_pages(text_by_page, tokens_by_page, tables_by_page)


def _load_v3(
    etl_output: "Any",
    tables_uri: str,
    reader: "Callable[..., Any]",
    text: bool,
    tokens: bool,
    tables: bool,
) -> EtlOutput:
    pages = get(etl_output, list, "pages")

    if text or tokens:
        text_by_page = map(lambda page: reader(get(page, str, "text")), pages)
    else:
        text_by_page = ()  # type: ignore[assignment]

    if tokens:
        tokens_by_page = map(lambda page: reader(get(page, str, "tokens")), pages)
    else:
        tokens_by_page = ()  # type: ignore[assignment]

    if tables:
        tables_by_page = reader(tables_uri)
    else:
        tables_by_page = ()

    return EtlOutput.from_pages(text_by_page, tokens_by_page, tables_by_page)


async def _load_v1_async(
    etl_output: "Any",
    tables_uri: str,
    reader: "Callable[..., Awaitable[Any]]",
    text: bool,
    tokens: bool,
    tables: bool,
) -> EtlOutput:
    if text or tokens:
        pages = [
            await reader(get(page, str, "page_info"))
            for page in get(etl_output, list, "pages")
        ]
        text_by_page = map(lambda page: get(page, str, "pages", 0, "text"), pages)
        tokens_by_page = map(lambda page: get(page, list, "tokens"), pages)
    else:
        text_by_page = ()  # type: ignore[assignment]
        tokens_by_page = ()  # type: ignore[assignment]

    if tables:
        tables_by_page = await reader(tables_uri)
    else:
        tables_by_page = ()

    return EtlOutput.from_pages(text_by_page, tokens_by_page, tables_by_page)


async def _load_v3_async(
    etl_output: "Any",
    tables_uri: str,
    reader: "Callable[..., Awaitable[Any]]",
    text: bool,
    tokens: bool,
    tables: bool,
) -> EtlOutput:
    pages = get(etl_output, list, "pages")

    if text or tokens:
        text_by_page = [await reader(get(page, str, "text")) for page in pages]
    else:
        text_by_page = ()  # type: ignore[assignment]

    if tokens:
        tokens_by_page = [await reader(get(page, str, "tokens")) for page in pages]
    else:
        tokens_by_page = ()  # type: ignore[assignment]

    if tables:
        tables_by_page = await reader(tables_uri)
    else:
        tables_by_page = ()

    return EtlOutput.from_pages(text_by_page, tokens_by_page, tables_by_page)
