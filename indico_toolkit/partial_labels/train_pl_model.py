"""
(Offline)
1. Modify code that retrieves objects from Review to write them all (or some portion) to S3
    within that cluster. Would need to work w/ ops to get bucket provisioned that we are
    allowed to read/write data from
2. Make sure that objects that are not retrieved are written to S3 in some other way. Likely
    need to dig deeper into CW data

Training
* Sample some data from review in S3. Split into train/test and train a partial labels model
    after combining w/ teach
    * Do this by creating a new dataset and model group. Test split will be a combination of
    review and teach, which is probably fine. Model metrics won't be exactly what we're
    looking for, but that's fine
* Expose API or script for comparing model metrics between original model and PL model
    * Determine if we should add new value matching metrics into somewhere more "official"
    than the solutions toolkit

Post Train
* Provide script or API for creating a new workflow with the updated model group
* Optionally provide script for comparing metrics between workflows, but this
    might not be required for the first pass

How to determine one vs many
* Can prepopulate based on statistics and then ask client to correct

APIs to sequence
* CreateDataset() w/ wait True
* CreateModelGroup() w/ wait True (or poll until model is done)
* ModelGroupPredict() on a holdout set for both original and new models for offline review comparison
* ListWorkflows() w/ dataset ID to find new workflow
    * Can you enable a workflow for review w/ the API?

Need to move model from DEV to PROD after training to create a prod workflow
https://indicodata.slack.com/archives/CLJGMCK3Q/p1626895835321200
"""
from typing import Dict, List, Tuple

from indico import IndicoClient, IndicoConfig
from indico.queries import SubmissionFilter
from indico_toolkit.indico_wrapper import IndicoWrapper, Workflow


def get_review_data(workflow: Workflow, workflow_id: int) -> Tuple[List[str], List[Dict], List[Dict]]:
    """
    Get review data from production workflow

    Args:
        workflow:
        workflow_id:

    Returns:
        text: Text from documents in review
        predictions: Predictions made on review docs prior to user corrections
        labels: Labels on review docs after user corrections
    """
    # TODO This will only get submissions w/ retrieved=False. Need to tweak otherwise
    # TODO Make sure this works if more than 1000 submissions, and won't crash anything
    submissions = workflow.get_complete_submission_objects(workflow_id=workflow_id)
    workflow_results = workflow.get_submission_results_from_ids(
        [sub.id for sub in submissions]
    )

    # Get predictions and final labels (post review) from workflow results
    # TODO Could also incorporate "diff" information from "post_reviews" key in the future
    #  if we want to treat predictions that are accepted or rejected via auto review differently
    text = []
    predictions = []
    labels = []
    for workflow_res in workflow_results:
        result = list(workflow_res.get("results", {}).get("document", {}).get("results", {}).values())[0]
        predictions.append(result.get("pre_review"))
        labels.append(result.get("final"))
        # Get document text
        doc_text = workflow.get_ondoc_ocr_from_etl_url(result["etl_output"])
        text.append(doc_text.full_text)

    return text, predictions, labels


def main(
    dev_host: str,
    dev_api_token_path: str,
    prod_host: str,
    prod_api_token_path: str,
    dev_dataset_id: int,
    dev_model_id: int,
    prod_workflow_id: int,
    max_review_docs: int = 1000,
    oversample_errs: bool = False,
):
    """

    Args:
        dev_host: Host URL for dev environment
        dev_api_token_path: API token path for dev env
        prod_host: Host URL for prod env
        prod_api_token_path: API token path for prod env
        dev_dataset_id: Dataset ID for dev dataset associated w/ prod workflow
        dev_model_id: Model ID for dev dataset associated w/ prod workflow
            TODO Should this be model group ID instead?
        prod_workflow_id: Workflow ID for prod workflow w/ review enabled
            TODO Will need to be reworked if we're keeping review docs in S3 instead
        max_review_docs: Maximum number of documents from review to add to dataset
            If max_review_docs is less than the number of docs that have been
            reviewed, sample from review
        oversample_errs: If True, sample more heavily from documents with more
            discrepancies between model predictions and ground truth

    Returns:
    """
    prod_client = IndicoClient(IndicoConfig(host=prod_host, api_token_path=prod_api_token_path))
    prod_workflow = Workflow(client=prod_client)
    text, predictions, labels = get_review_data(prod_workflow, prod_workflow_id)

    # Postprocess

    # Add to teach
    dev_client = IndicoClient(IndicoConfig(host=dev_host, api_token_path=dev_api_token_path))
    dev_workflow = Workflow(client=dev_client)

    # workflow 279 for CW build env





if __name__ == "__main__":
    main()
