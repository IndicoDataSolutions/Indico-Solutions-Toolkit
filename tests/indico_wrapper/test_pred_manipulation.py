import pytest
import os
import json

from indico_toolkit.indico_wrapper.pred_manipulation import ManipulatePreds


@pytest.fixture(scope="session")
def manipulation_preds(testdir_file_path):
    print(testdir_file_path)
    with open(
        os.path.join(
            testdir_file_path,
            "indico_wrapper/data/pred_manipulation/manip_preds.json",
        ),
        "r",
    ) as f:
        preds = json.load(f)
    return preds


@pytest.fixture(scope="session")
def manipulation_tokens(testdir_file_path):
    print(testdir_file_path)
    with open(
        os.path.join(
            testdir_file_path,
            "indico_wrapper/data/pred_manipulation/manip_tokens.json",
        ),
        "r",
    ) as f:
        ocr_tokens = json.load(f)
    return ocr_tokens


@pytest.mark.parametrize(
    "start,end",
    [
        (26, 32),
        (75, 95),
    ],
)
def test_expand_predictions(manipulation_tokens, manipulation_preds, start, end):
    for pred in manipulation_preds:
        if pred["start"] == start and pred["end"] == end:
            original_prediction = pred["text"]
    manipulate = ManipulatePreds(manipulation_tokens, manipulation_preds)
    updated_predictions = manipulate.expand_predictions(start, end)
    assert updated_predictions["text"] != original_prediction


@pytest.mark.parametrize(
    "start,end,search_tokens,distance",
    [
        (26, 32, ["NUMBER"], 5),
        (73, 80, ["YEAR", "REGISTERED"], 10),
    ],
)
def test_token_nearby_true(
    manipulation_tokens, manipulation_preds, start, end, search_tokens, distance
):
    manipulate = ManipulatePreds(manipulation_tokens, manipulation_preds)
    is_nearby = manipulate.is_token_nearby(start, end, search_tokens, distance)
    assert is_nearby == True


@pytest.mark.parametrize(
    "start,end,search_tokens,distance",
    [
        (26, 32, ["Indico"], 5),  # not found
        (73, 80, ["123", "Sucker"], 2),  # not found
    ],
)
def test_token_nearby_false(
    manipulation_tokens, manipulation_preds, start, end, search_tokens, distance
):
    manipulate = ManipulatePreds(manipulation_tokens, manipulation_preds)
    is_nearby = manipulate.is_token_nearby(start, end, search_tokens, distance)
    assert is_nearby == False


@pytest.mark.parametrize(
    "start,end,search_tokens,distance",
    [
        (263939, 33032, ["Indico"], 5),  # out of bounds
        (1939, 89913, ["123", "Sucker"], 2),  # out of bounds
    ],
)
def test_token_nearby_error(
    manipulation_tokens, manipulation_preds, start, end, search_tokens, distance
):
    manipulate = ManipulatePreds(manipulation_tokens, manipulation_preds)
    with pytest.raises(ValueError):
        manipulate.is_token_nearby(start, end, search_tokens, distance)
