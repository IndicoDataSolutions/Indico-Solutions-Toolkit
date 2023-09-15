import fire
import os
import json
import pandas as pd
from tqdm import tqdm
from indico import IndicoClient, IndicoConfig

from download_helpers import *
from table_helpers import *


class TableAssociator:
    def __init__(
        self,
        labelset_name,
        host,
        api_token_path,
        dataset_id,
        json_output_file_name,
        labelset_id=None,
        label_col=None,
        text_col=None,
        filename_col=None,
        csv_path=None,
    ):
        self.name = labelset_name
        self.host = host
        self.api_token_path = api_token_path
        self.dataset_id = dataset_id
        self.labelset_id = labelset_id
        self.label_col = label_col
        self.text_col = text_col
        self.filename_col = filename_col
        self.csv_path = csv_path
        self.my_config = IndicoConfig(
            host=self.host,
            api_token_path=self.api_token_path,
        )
        self.client = IndicoClient(config=self.my_config)
        self.output = json_output_file_name

    def run(self):
        raw_export = get_export(self.client, self.dataset_id, self.labelset_id)
        if self.csv_path:
            export_records = save_to_csv(
                self.label_col,
                raw_export,
                self.name,
                self.csv_path,
                self.filename_col,
                self.client,
                self.text_col,
            )
        else:
            export_records = generate_export_records(
                self.label_col,
                raw_export,
                self.filename_col,
                self.name,
                self.client,
                self.text_col,
            )

        associations_by_file = []
        for record in export_records:
            file_name = record["document_path"].split("/")[-1].split(".")[0]
            try:
                labels = json.loads(record["labels"])
            except TypeError:
                print(f"No labels for {file_name}.")
                continue
            ocr = json.loads(record["ocr"])
            tables_with_labels = self.get_tables_with_labels(labels, ocr)
            associations_by_page = {}
            for t in tqdm(tables_with_labels):
                associations = []
                for table in t["tables"]:
                    indexed = {i: c for i, c in enumerate(table["cells"])}
                    representation = json_to_html_table(indexed)
                    rows = get_rows(indexed)
                    cols = get_columns(indexed)
                    if not t["labels"]:
                        continue
                    label_map = self.map_label_to_cells(t["labels"], indexed)
                    associations.append(
                        {
                            "all_cells": indexed,
                            "table_representation": representation,
                            "row_association": rows,
                            "column_association": cols,
                            "label_map": label_map,
                        }
                    )
                associations_by_page[t["page"]] = associations
            associations_by_file.append(
                {"filename": file_name, "associations_by_page": associations_by_page}
            )

        with open(self.output, "w") as f:
            json.dump(associations_by_file, f)

    def get_tables_with_labels(self, labels, ocr):
        tables_with_labels = []
        for i, page in enumerate(ocr):
            if len(page["tables"]) == 0:
                continue
            else:
                tables_on_page = page["tables"]
                page_start = page["pages"][0]["doc_offset"]["start"]
                page_end = page["pages"][0]["doc_offset"]["end"]
                labels_on_page = []
                for l in labels:
                    if l["start"] >= page_start and l["end"] <= page_end:
                        labels_on_page.append(l)
                tables_with_labels.append(
                    {"page": i, "tables": tables_on_page, "labels": labels_on_page}
                )
        return tables_with_labels

    def map_label_to_cells(self, labels, json_data):
        associations = []

        for label_data in labels:
            label_start = label_data["start"]
            label_end = label_data["end"]
            label_name = label_data["label"]

            matching_cells = {}

            for cell_index, cell_data in json_data.items():
                if not cell_data["doc_offsets"]:
                    continue
                cell_start = cell_data["doc_offsets"][0]["start"]
                cell_end = cell_data["doc_offsets"][0]["end"]

                if label_start >= cell_start and label_end <= cell_end:
                    matching_cells[cell_index] = cell_data

            association = CellLabelAssociation(label_name, matching_cells)
            associations.append(association.to_dict())

        return associations


if __name__ == "__main__":
    assoc = TableAssociator(
        labelset_name="treaty",
        host="dev-ci.us-east-2.indico-dev.indico.io/",
        api_token_path="dev_token.txt",
        dataset_id=8006,
        json_output_file_name="treaty_output.json",
        labelset_id=12970,
        label_col="Treaty Table Field Extraction - TABLE Model",
        text_col="document",
        filename_col="file_name",
        csv_path="treaty_records.csv",
    )
    assoc.run()
