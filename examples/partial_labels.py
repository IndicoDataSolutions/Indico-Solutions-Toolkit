"""
TODO How to revert to previous model (in the same model group) if necessary?

Outside of Script
* Expose API or script for comparing model metrics between original model and PL model
    * Determine if we should add new value matching metrics into somewhere more "official"
    than the solutions toolkit
* Optionally provide script for comparing metrics between workflows, but this
    might not be required for the first pass
* Determine one vs many
    * Can prepopulate based on statistics and then ask client to correct
* Need to move model from DEV to PROD after training to create a prod workflow
    * https://indicodata.slack.com/archives/CLJGMCK3Q/p1626895835321200
"""
import argparse
from datetime import datetime, timedelta

from indico import IndicoClient, IndicoConfig
from indico_toolkit.indico_wrapper import workflow
from indico_toolkit.staggered_loop import StaggeredLoop


def create_argument_parser() -> argparse.ArgumentParser:
    """
    Argument parser for training a donor model
    """
    parser = argparse.ArgumentParser(description="Train a partial labels model")
    parser.add_argument(
        "--dev_host",
        required=False,
        help="Host URL for DEV Indico IPA environment",
    )
    parser.add_argument(
        "--dev_api_token_path",
        required=False,
        help="Path to DEV API token to authenticate to dev_host",
    )
    parser.add_argument(
        "--prod_host",
        required=False,
        help="Host URL for PROD Indico IPA environment",
    )
    parser.add_argument(
        "--prod_api_token_path",
        required=False,
        help="Path to PROD API token to authenticate to prod_host",
    )
    parser.add_argument(
        "--dev_model_group_id",
        required=False,
        help="Model Group ID for dev dataset / teach task",
    )
    parser.add_argument(
        "--prod_workflow_id",
        required=False,
        help="Workflow ID for prod workflow with review data",
    )
    return parser


def main(
    dev_host: str,
    dev_api_token_path: str,
    prod_host: str,
    prod_api_token_path: str,
    dev_model_group_id: int,
    prod_workflow_id: int,
    oversample_errs: bool = False,
):
    """
    End to end function to data that has been submitted to a production workflow
    and reviewed to an existing dataset, teach task, and extraction model

    TODO
     * Use max_review_docs and oversample_errs arguments

    Args:
        dev_host: Host URL for dev environment
        dev_api_token_path: API token path for dev env
        prod_host: Host URL for prod env
        prod_api_token_path: API token path for prod env
        dev_model_group_id: Model Group ID for dev dataset / teach task
        prod_workflow_id: Workflow ID for prod workflow w/ review enabled
        max_review_docs: Maximum number of documents from review to add to dataset
            If max_review_docs is less than the number of docs that have been
            reviewed, sample from review
        oversample_errs: If True, sample more heavily from documents with more
            discrepancies between model predictions and ground truth
    """
    # Connect to dev
    dev_client = IndicoClient(
        IndicoConfig(host=dev_host, api_token_path=dev_api_token_path)
    )
    dev_stagger = StaggeredLoop(client=dev_client)

    # Get dataset details to determine when dataset was last updated. This will serve
    # as a filter to prevent adding duplicate review data
    # TODO: use this again

    related = dev_stagger.model_group_details(model_group_id=dev_model_group_id)
    dev_dataset_id = related["dataset_id"]

    # TODO: use date last modified
    dataset_details = dev_stagger.get_dataset_details(dataset_id=dev_dataset_id)

    # Connect to prod
    prod_client = IndicoClient(
        IndicoConfig(host=prod_host, api_token_path=prod_api_token_path)
    )
    prod_stagger = StaggeredLoop(client=prod_client)

    # Pull review data from prod workflow
    since = datetime.now() - timedelta(days=7)
    workflow_results = prod_stagger.get_review_data(
        workflow_id=prod_workflow_id,
        update_date=since,
    )
    doc_paths = prod_stagger.get_document_bytes()
    doc_texts = prod_stagger.get_submission_full_text()

    # StaggeredLoop class extends IndicoClient, so strictly has to connect to
    # only one environment. As a result, we set the workflow_results attribute
    # of the dev instance of the class using the review data pulled from prod.
    dev_stagger.set_workflow_results(workflow_results, doc_paths, doc_texts)

    # Postprocess and sample review data
    dev_stagger.process_review_data()
    dev_stagger.sample_data(sample_ratio=1, oversample_errors=oversample_errs)

    # # # Add data to dev dataset and retrain model
    dev_stagger.add_data(model_group_id=dev_model_group_id, partial=True)

    # Not necessary to update model settings because default is to use partially
    # labeled data for training when provided
    dev_stagger.retrain_model(model_group_id=dev_model_group_id)


if __name__ == "__main__":
    parser = create_argument_parser()
    args = parser.parse_args()

    main(
        dev_host=args.dev_host,
        dev_api_token_path=args.dev_api_token_path,
        prod_host=args.prod_host,
        prod_api_token_path=args.prod_api_token_path,
        dev_model_group_id=args.dev_model_group_id,
        prod_workflow_id=args.prod_workflow_id,
    )
