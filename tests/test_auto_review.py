from solutions_toolkit.auto_review import ReviewConfiguration, Reviewer
from tests.conftest import create_pred_label_map


min_max_length = 6
ACCEPTED = "accepted"
REJECTED = "rejected"


def test_reviewer(auto_review_field_config, auto_review_preds):
    review_config = ReviewConfiguration(auto_review_field_config)
    reviewer = Reviewer(auto_review_preds, review_config)
    reviewer.apply_reviews()
    preds = reviewer.updated_predictions
    pred_map = create_pred_label_map(preds)
    for pred in pred_map["accept_by_all_match_and_confidence"]:
        assert pred[ACCEPTED] == True
    for pred in pred_map["reject_by_confidence"]:
        if pred["text"] == "low":
            assert pred[REJECTED] == True
        else:
            assert pred[ACCEPTED] == True
    for pred in pred_map["reject_by_min_character_length"]:
        if len(pred["text"]) < min_max_length:
            assert pred[REJECTED] == True
        else:
            assert REJECTED not in pred.keys()
    for pred in pred_map["reject_by_max_character_length"]:
        if len(pred["text"]) > min_max_length:
            assert pred[REJECTED] == True
        else:
            assert REJECTED not in pred.keys()
    for pred in pred_map["split_merged_values"]:
        assert pred[ACCEPTED] == True
    assert len(pred_map["split_merged_values"]) == 4
    assert "remove_by_confidence" not in pred.keys()


