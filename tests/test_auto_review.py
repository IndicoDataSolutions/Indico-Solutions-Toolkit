from solutions_toolkit.auto_review import ReviewConfiguration, Reviewer
from tests.conftest import create_pred_label_map


def test_reviewer(auto_review_field_config, auto_review_preds):
    review_config = ReviewConfiguration(auto_review_field_config)
    reviewer = Reviewer(auto_review_preds, review_config)
    reviewer.apply_reviews()
    preds = reviewer.updated_predictions
    pred_map = create_pred_label_map(preds)
    for pred in pred_map["name"]:
        assert pred["accepted"] == True
    assert len(pred_map["price"]) == 3
    for pred in pred_map["price"]:
        assert pred["accepted"] == True
    for pred in pred_map["age"]:
        assert pred["rejected"] == True
