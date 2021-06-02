from indico_toolkit.association import LineItems

# Example extraction prediction result from model/workflow (use full list of predictions)
PREDICTIONS = [
        {"label": "line_date", "start": 12, "end": 18, "text": "1/2/2021"},
        {"label": "line_value", "start": 20, "end": 23, "text": "$12"},
    ]
# Example OCR Token, can be retrieved from workflow result with Workflow.get_ondoc_ocr_from_etl_url 
OCR_TOKENS = [
        {
        "page_num": 0,
        "position": {
            "bbBot": 100,
            "bbTop": 0,
            "bbLeft": 423,
            "bbRight": 833
            },
        },
    ]   

litems = LineItems(
        predictions=PREDICTIONS,
         # fields from your model that should be treated as line items
        line_item_fields=["line_value", "line_date"],
    )

litems.get_bounding_boxes(ocr_tokens=OCR_TOKENS)
# adds "row_number", page_num, and bounding box metadata to every line_item_fields prediction dictionary
litems.assign_row_number()
# all predictions with added metadata -> List[dict]
print(litems.updated_predictions)
# only line item predictions grouped together -> List[List[dict]]
print(litems.grouped_line_items)