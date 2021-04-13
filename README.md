# Indico-Solutions-Toolkit
A library to assist with Indico IPA development

### Tests
To see test coverage
```
coverage run --omit 'venv/*' -m pytest
coverage report -m
```

## Examples

### Row Association / Line Items

How to add row_number key to your predictions
```
from solutions_toolkit.row_association import Association

litems = Association(
        line_item_fields=["line_value", "line_date"], 
        predictions=[{"label": "line_date", "start": 12, "text": "1/2/2021".....}]
    )

litems.get_bounding_boxes(ocr_tokens=[{"postion"...,},])
litems.assign_row_number()

updated_preds: List[dict] = litems.updated_predictions
```

### Scripted/Auto Review

How to auto-review predictions
```
from solutions_toolkit.auto_review import ReviewConfiguration, Reviewer

field_config = [
    {
        "function": "accept_by_confidence",
        "kwargs": {
            "label": ["Name"],
            "conf_threshold": 0.95
        }
    },
    ...
]
review_config = ReviewConfiguration(field_config)

reviewer = Reviewer(
        predictions=[{"label": "Name", "start": 12, "text": "Jane Doe".....}],
        review_config=review_config
    )
reviewer.apply_reviews()
updated_preds: List[dict] = reviewer.updated_predictions
```

### Making API calls

How to make workflow related API calls
```
from solutions_toolkit.indico_wrapper import WorkFlow

host = "app.indico.io"
api_token_path = "/path/to/indico_api_token.txt"
workflow_id = 767

wflow = WorkFlow(host, api_token_path=api_token_path)
# submit a batch of documents to a workflow
submission_ids = wflow.submit_documents_to_workflow(workflow_id, ["./path/to/mydoc.pdf",...])
# get predictions for a particular document
wflow_result = wflow.get_submission_result_from_id(submission_ids[0])
```