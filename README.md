
# Indico-Solutions-Toolkit
A library to assist with Indico IPA development

[![Build Status][build-image]][build-url]


### Tests
To see test coverage
```
coverage run --omit 'venv/*' -m pytest
coverage report -m
```

### Examples 
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

How to use the OCR modules
```
from solutions_toolkit.ocr import StandardOcr

job = client.call(DocumentExtraction(files=[src_path], json_config={"preset_config": "standard"}))
job = client.call(JobStatus(id=job[0].id, wait=True))
extracted_data = client.call(RetrieveStorageObject(job.result))
results = StandardOcr(extracted_data)

print(results.full_text)
print(results.page_results)
```

<!-- Badges -->
[build-url]: https://github.com/IndicoDataSolutions/Indico-Solutions-Toolkit/actions/workflows/build.yml
[build-image]: https://github.com/IndicoDataSolutions/Indico-Solutions-Toolkit/actions/workflows/build.yml/badge.svg