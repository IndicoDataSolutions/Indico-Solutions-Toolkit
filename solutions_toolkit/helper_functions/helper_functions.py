from pathlib import Path
import tempfile
import shutil
from PyPDF2 import PdfFileReader, PdfFileWriter
import sys
import random
from indico.queries import (
    DocumentExtraction,
    JobStatus,
    RetrieveStorageObject,
    ModelGroupPredict,
)
from indico.queries.datasets import CreateDataset
from solutions_toolkit.indico_wrapper import IndicoWrapper
import json


def create_staging_file(file: str, staging_file_handle):

    with open(file, "rb") as pdf_file:
        shutil.copyfileobj(pdf_file, staging_file_handle)
        staging_file_handle.seek(0)

    return staging_file_handle


def split_and_save_pdf_as_individual_pages(
    file_paths: list, results_dir: Path, file_dir: Path
):
    """
    Save the .pdf files in file_paths page by page from file_dir to results_dir

    """

    for file in file_paths:

        try:
            staging_file_handle = create_staging_file(tempfile.TemporaryFile())
        except:
            print(" Unable to process " + str(file) + " " + str(sys.exc_info()[0]))
            continue

        try:
            pdf_file_read = PdfFileReader(staging_file_handle, strict=False)
        except:
            print(" Unable to read pdf: " + str(file) + " " + str(sys.exc_info()[0]))
            continue

        if pdf_file_read.isEncrypted:
            try:
                pdf_file_read.decrypt("")
            except NotImplementedError:
                print(" Unable to decrypt: " + str(file))
                continue

        try:
            number_of_pages = range(pdf_file_read.numPages)
        except:
            print(
                " Unable to determine the number of pages: "
                + str(file)
                + " "
                + str(sys.exc_info()[0])
            )
            continue

        for page in number_of_pages:
            result_pdf_filepath = generate_output_filepath_for_page(
                page, file, results_dir, file_dir
            )
            try:
                result_pdf = PdfFileWriter()
                result_pdf.addPage(pdf_file_read.getPage(page))
                with open(result_pdf_filepath, "wb") as result_pdf_output:
                    result_pdf.write(result_pdf_output)
            except Exception as error_handle:
                print(
                    " Unable to save page: "
                    + str(result_pdf_filepath)
                    + str(error_handle)
                )
                continue
        staging_file_handle.close()

    return


def generate_output_filepath_for_page(page, file, results_dir: Path, file_dir: Path):

    result_pdf_filepath_suffix = "_" + "0" * (3 - len(str(page))) + str(page) + ".pdf"
    result_pdf_filepath = Path(
        str(results_dir / Path(file).relative_to(file_dir)).replace(
            ".pdf", result_pdf_filepath_suffix
        )
    )
    result_pdf_filepath.parent.mkdir(parents=True, exist_ok=True)

    return result_pdf_filepath


def is_num_pages_less_than_threshold(file_paths, page_number_threshold):
    """
    Computes the number of pages for each file in a batch
    and returns whether the batch is within the threshold

    """

    for file in file_paths:
        try:
            staging_file_handle = create_staging_file(tempfile.TemporaryFile())
        except:
            print(" Unable to process " + str(file) + " " + str(sys.exc_info()[0]))
            continue

        try:
            pdf = PdfFileReader(staging_file_handle, strict=False)
        except:
            print(" Unable to read pdf: " + str(file) + " " + str(sys.exc_info()[0]))
            continue

        if pdf.isEncrypted:
            try:
                pdf.decrypt("")
            except NotImplementedError:
                print(" Unable to decrypt: " + str(file))
                continue

        try:
            page_numbers = pdf.numPages
        except:
            print(
                " Unable to determine the number of pages: "
                + str(file)
                + " "
                + str(sys.exc_info()[0])
            )
            continue

        if page_numbers > page_number_threshold:
            print(" More than 50 pages in ", str(file))
            return False

    return True


def extract_documents(file_paths: list, client, preset_config: str, vdp: bool):
    """
    Send a batch for extraction/OCR and return the prediction results

    """

    if len(file_paths) < 1:
        return []

    print(" Sent for file extraction: " + str(file_paths))
    try:
        job = client.call(
            DocumentExtraction(
                files=file_paths,
                json_config={"preset_config": preset_config, "vdp": vdp},
            )
        )
    except:
        print(
            " Document Extraction failed for: "
            + str(file_paths)
            + " due to: "
            + str(sys.exc_info()[0])
        )
        return []

    batch_of_results = []
    for i in range(len(file_paths)):
        job_file = client.call(JobStatus(id=job[i].id))
        if job_file.status == "SUCCESS":
            batch_of_results.append(client.call(RetrieveStorageObject(job_file.result)))
            print(" Successfully extracted file: " + str(file_paths[i]))
        else:
            print(" File extraction unsuccesful: " + str(file_paths[i]))
    return batch_of_results


def upload_files(
    filepaths: list, batch_size: int, dataset_name: str, dataset_type: str, client
):
    """
    Create and upload a dataset to IPA

    """

    if len(filepaths) < 1:
        return

    docs_to_upload = filepaths

    if batch_size < len(docs_to_upload):
        docs_to_upload = random.sample(docs_to_upload, k=batch_size)

    try:
        dataset = CreateDataset(dataset_name, docs_to_upload, dataset_type=dataset_type)
        client.call(dataset)
        print(f" Uploaded dataset: {dataset_name}")
    except OSError:
        print(" Unable to create dataset " + str(sys.exc_info()[0]))
        return

    return


def get_model_predictions_for_doc_extraction_results(batch: list, client):
    """
    Download predictions for doc extraction results

    """

    batch_samples = ["a"] * len(batch)
    for i, file in enumerate(batch):
        try:
            with open(file, "r") as f:
                doc_extraction_result = json.load(f)
        except:
            print("Unable to load json file due to " + str(sys.exc_info()[0]))

        extracted_text = "\n".join(
            page_text["pages"][0]["text"] for page_text in doc_extraction_result
        )
        batch_samples[i] = extracted_text

    try:
        job = client.call(
            ModelGroupPredict(
                model_id=294,
                data=batch_samples,
            )
        )

    except:
        print("Unable to get model predictions due to " + str(sys.exc_info()[0]))
        return

    return client.call(JobStatus(id=job.id, wait=True)).result


def submit_strings_to_workflow(text: list, workflow_id: int, indico_wrapper):
    """
    Upload a batch to the Review Queue

    """

    submission_ids = []

    try:
        batch_submission_ids = indico_wrapper.upload_to_workflow(workflow_id, text)
        submission_ids.append(batch_submission_ids)
        indico_wrapper.wait_for_submission(
            submission_ids=batch_submission_ids, timeout=240
        )
    except:
        print("Unable to upload dataset to workflow due to " + str(sys.exc_info()[0]))
        return []

    return submission_ids


def get_predictions_from_submission_to_workfow(indico_wrapper, ID: str):
    """
    Download predictions for a batch

    """

    submissions = indico_wrapper.get_submissions(ID, "COMPLETE", retrieved_flag=False)
    submission_results = []

    for submission in submissions:
        result = indico_wrapper.get_submission_results(submission)
        submission_results.append(result)

    return submission_results