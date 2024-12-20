import json
from pathlib import Path

import pytest

from indico_toolkit import etloutput

data_folder = Path(__file__).parent.parent / "data" / "etloutput"


def read_url(url: str) -> object:
    storage_folder_path = url.split("/storage/submission/")[-1]
    file_path = data_folder / storage_folder_path

    if file_path.suffix.casefold() == ".json":
        return json.loads(file_path.read_text())
    else:
        return file_path.read_text()


@pytest.mark.parametrize("etl_output_file", list(data_folder.rglob("etl_output.json")))
def test_file_load(etl_output_file: Path) -> None:
    try:
        etl_output = etloutput.load(str(etl_output_file), reader=read_url, tables=True)
    except FileNotFoundError:
        etl_output = etloutput.load(str(etl_output_file), reader=read_url, tables=False)

    page_count = len(etl_output.text_on_page)
    char_count = len(etl_output.text)
    token_count = len(etl_output.tokens)
    table_count = len(etl_output.tables)

    assert page_count == 6
    assert char_count in (6466, 6494)
    assert token_count in (948, 978)
    assert table_count in (0, 6)
