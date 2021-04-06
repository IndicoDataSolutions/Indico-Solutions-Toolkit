# Indico-Solutions-Toolkit
A library to assist with Indico IPA development

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

Auto-review predictions
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