from solutions_toolkit.auto_review import ReviewConfiguration, Reviewer
from tests.conftest import create_pred_label_map


min_max_length = 6
ACCEPTED = "accepted"
REJECTED = "rejected"


def accept_if_match(predictions, match_text: str, labels: list = None):
    """Custom function to pass into ReviewConfiguration"""
    for pred in predictions:
        if REJECTED not in pred:
            if labels != None and pred["label"] not in labels:
                continue
            if pred["text"] == match_text:
                pred["accepted"] = True
    return predictions


def test_reviewer(auto_review_field_config, auto_review_preds):
    custom_functions = {"accept_if_match": accept_if_match}
    review_config = ReviewConfiguration(auto_review_field_config, custom_functions)
    reviewer = Reviewer(auto_review_preds, review_config)
    reviewer.apply_reviews()
    preds = reviewer.updated_predictions
    pred_map = create_pred_label_map(preds)
    for pred in pred_map["accept_by_all_match_and_confidence"]:
        assert pred[ACCEPTED] == True
    for pred in pred_map["low_conf_accept_by_all_match_and_confidence"]:
        assert ACCEPTED not in pred
    for pred in pred_map["no_match_accept_by_all_match_and_confidence"]:
        assert ACCEPTED not in pred
    for pred in pred_map["reject_by_confidence"]:
        if pred["text"] == "low":
            assert pred[REJECTED] == True
        else:
            assert pred[ACCEPTED] == True
    for pred in pred_map["reject_by_min_character_length"]:
        if len(pred["text"]) < min_max_length:
            assert pred[REJECTED] == True
        else:
            assert REJECTED not in pred
    for pred in pred_map["reject_by_max_character_length"]:
        if len(pred["text"]) > min_max_length:
            assert pred[REJECTED] == True
        else:
            assert REJECTED not in pred
    for pred in pred_map["accept_if_match"]:
        assert pred["accepted"] == True
    assert "remove_by_confidence" not in pred
