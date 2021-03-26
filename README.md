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