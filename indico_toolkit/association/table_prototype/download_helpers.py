from indico.queries import (
    RetrieveStorageObject,
    GetDataset,
    DownloadExport,
    CreateExport,
)
from indico.client import GraphQLRequest

import os
import json
import pandas as pd
from tqdm import tqdm


class GraphQLMagic(GraphQLRequest):
    def __init__(self, *args, **kwargs):
        super().__init__(query=self.query, variables=kwargs)


class GetLabelsetName(GraphQLMagic):
    query = """
    query GetTargetNames($datasetId:Int!){
        dataset(id:$datasetId) {
            labelsets {
                id
                name
            }
        }
    }
    """


class GetDatafileIDs(GraphQLMagic):
    query = """
    query getDatafileIDs($datasetId: Int!){
        dataset(id: $datasetId) {
            files {
                fileType
                id
                name
                rainbowUrl
            }
        }
    }
    """


class GetDatafileByID(GraphQLMagic):
    query = """
    query getDatafileById($datafileId: Int!) {
        datafile(datafileId: $datafileId) {
            pages {
                id
                pageInfo
                image
                pageNum
            }
        }
    }
    """


class GetLabelsetName(GraphQLMagic):
    query = """
    query GetTargetNames($datasetId:Int!){
        dataset(id:$datasetId) {
            labelsets {
                id
                name
            }
        }
    }
    """


def get_ocr_by_datafile_id(client, datafile_id, dataset_dir, filename):
    """
    Given an Indico client and a datafile ID, download OCR data for all pages
    along with page image PNGs for each page.
    """
    datafile_meta = client.call(GetDatafileByID(datafileId=datafile_id))
    page_ocrs = []
    local_page_json_dir = os.path.join(dataset_dir, "jsons", filename)
    os.makedirs(local_page_json_dir, exist_ok=True)
    for page in datafile_meta["datafile"]["pages"]:
        page_json_file = os.path.join(
            local_page_json_dir, f"page_{page['pageNum']}.json"
        )
        if os.path.exists(page_json_file):
            page_ocr = json.load(open(page_json_file))
        else:
            page_ocr = client.call(RetrieveStorageObject(page["pageInfo"]))
        with open(page_json_file, "w") as fd:
            json.dump(page_ocr, fd)
        page_ocrs.append(page_ocr)
    return page_ocrs


def text_from_ocr(page_ocrs):
    return "\n".join(page["pages"][0]["text"] for page in page_ocrs)


def reformat_labels(labels, document):
    spans_labels = json.loads(labels)
    old_labels_i = []
    for target in spans_labels["targets"]:
        old_labels_i.append(
            {
                "label": target["label"],
                "start": min(l["start"] for l in target["spans"]),
                "end": max(l["end"] for l in target["spans"]),
            }
        )
        old_labels_i[-1]["text"] = document[
            old_labels_i[-1]["start"] : old_labels_i[-1]["end"]
        ]
    return json.dumps(old_labels_i)


def get_export(client, dataset_id, labelset_id=None):
    # Get dataset object
    dataset = client.call(GetDataset(id=dataset_id))

    if labelset_id is None and dataset.labelsets:
        labelset_id = dataset.labelsets[0].id

    if labelset_id is not None:
        # Create export object using dataset's id and labelset id
        print("Creating export using Indico API...")
        export = client.call(
            CreateExport(
                dataset_id=dataset.id,
                labelset_id=labelset_id,
                file_info=True,
                wait=True,
            )
        )

        # Use export object to download as pandas csv
        print("Downloading export...")
        df = client.call(DownloadExport(export.id))
        df = df.rename(columns=lambda col: col.rsplit("_", 1)[0])
    else:
        raise ValueError(f"{labelset_id} is required to generate export.")

    return df


def save_to_csv(label_col, raw_export, name, csv_path, filename_col, client, text_col):
    output_records = generate_export_records(
        label_col, raw_export, filename_col, name, client, text_col
    )
    csv_path = os.path.join(name, csv_path)
    print("Creating CSV...")
    pd.DataFrame.from_records(output_records).to_csv(csv_path, index=False)
    return output_records


def generate_export_records(
    label_col, raw_export, filename_col, labelset_name, client, text_col
):
    records = raw_export.to_dict("records")
    os.makedirs(os.path.join(labelset_name, "files"), exist_ok=True)
    output_records = []
    for _, row in enumerate(tqdm(records)):
        filename = os.path.splitext(os.path.basename(row[filename_col]))[0]
        document_path = os.path.join(
            labelset_name, "files", filename + "." + row["file_name"].split(".")[-1]
        )
        page_ocrs = get_ocr_by_datafile_id(
            client, row["file_id"], dataset_dir=labelset_name, filename=filename
        )

        # Try to get text from export, but fallback to reconstructing from page OCR
        if text_col in row:
            text = row[text_col]
        else:
            text = text_from_ocr(page_ocrs)

        # DF doesn't have labels or labels are null for a file
        if label_col not in row or pd.isna(row[label_col]):
            labels = None
        else:
            labels = reformat_labels(row[label_col], text)

        output_record = {
            "ocr": json.dumps(page_ocrs),
            "text": text,
            "labels": labels,
        }
        output_record["document_path"] = document_path

        try:
            with open(document_path, "wb") as fp:
                fp.write(client.call(RetrieveStorageObject(row["file_url"])))
        except Exception as e:
            print(row["file_url"])

        output_records.append(output_record)
    return output_records
