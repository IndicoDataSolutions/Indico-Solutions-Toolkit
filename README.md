# Indico-Solutions-Toolkit
A library to assist with Indico IPA development


Example: 
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

Example:
How to use the IndicoWrapper
```
from solutions_toolkit.indico_wrapper import IndicoWrapper

host = "app.indico.io"
api_token_path = "/path/to/token.txt"
workflow_id = 123

indico_wrapper = IndicoWrapper(host, api_token_path)


submissions = indico_wrapper.get_submissions(workflow_id, "COMPLETE")
sub_results = indico_wrapper.get_submission_results(submissions[0])
```