from typing import List


ACCEPTED = "accepted"
REJECTED = "rejected"


def reject_by_confidence(
    predictions: List[dict], label=None, conf_threshold=0.50
) -> List[dict]:
    """
    Adds rejected:True kvp for predictions below conf_threshold
    Returns:
    predictions List[dict]: all predictions
    """
    for prediction in predictions:
        if prediction.get(REJECTED) is None:
            if label != None and prediction["label"] != label:
                continue
            if prediction["confidence"][prediction["label"]] < conf_threshold:
                prediction[REJECTED] = True
                _ = prediction.pop(ACCEPTED, None)
    return predictions


def remove_by_confidence(
    predictions: List[dict], label=None, conf_threshold=0.50
) -> List[dict]:
    """
    Returns:
    updated_predictions List[dict]: predictions above conf_threshold
    """
    for prediction in predictions:
        if prediction.get(REJECTED) is None:
            if label != None and prediction["label"] != label:
                continue
            if prediction["confidence"][prediction["label"]] < conf_threshold:
                predictions.remove(prediction)
    return predictions


def accept_by_confidence(
    predictions: List[dict], label=None, conf_threshold=0.98
) -> List[dict]:
    """
    Adds accepted:True kvp for predictions above conf_threshold
    Returns:
    predictions List[dict]: all predictions
    """
    for prediction in predictions:
        if prediction.get(REJECTED) is None:
            if label != None and prediction["label"] != label:
                continue
            if prediction["confidence"][prediction["label"]] > conf_threshold:
                prediction[ACCEPTED] = True
    return predictions


def accept_by_all_match_and_confidence(
    predictions: List[dict], label: str, conf_threshold=0.98
):
    """
    Accepts all predictions for a class if all their values are all the same,
    and all their confidence is above conf_threshold
    Returns:
    predictions List[dict]: all predictions
    """
    pred_values = set()
    for pred in predictions:
        if pred.get(REJECTED) is None:
            if label != None and pred["label"] != label:
                continue
            if pred["confidence"][label] > conf_threshold:
                pred_values.add(pred["text"])

    if len(pred_values) == 1:
        text = pred_values.pop()
        for pred in predictions:
            if pred["text"] == text:
                if not pred["confidence"][label] > conf_threshold:
                    return predictions

        for pred in predictions:
            if pred["text"] == text:
                pred[ACCEPTED] = True
    return predictions


def reject_by_min_character_length(
    predictions: List[dict], label=None, min_length_threshold=3
) -> List[dict]:
    """
    Adds rejected:True kvp for predictions shorter than min_length_threshold
    Returns:
    predictions List[dict]: all predictions
    """
    for prediction in predictions:
        if label == None or label == prediction["label"]:
            if len(prediction["text"]) < min_length_threshold:
                prediction[REJECTED] = True
    return predictions


def reject_by_max_character_length(
    predictions: List[dict], label=None, max_length_threshold=10
) -> List[dict]:
    """
    Adds rejected:True kvp for predictions longer than max_length_threshold
    Returns:
    predictions List[dict]: all prediction
    """
    for prediction in predictions:
        if label == None or label == prediction["label"]:
            if len(prediction["text"]) > max_length_threshold:
                prediction[REJECTED] = True
    return predictions


def split_merged_values(predictions: List[dict], split_filter=None) -> List[dict]:
    """
    Splits merged predictions and updates indexes
    Returns:
    updated_predictions List[dict]: all predictions
    """
    updated_predictions = []
    for pred in predictions:
        merged_text = pred["text"]
        start = pred["start"]
        if split_filter:
            split_text = merged_text.split(split_filter)
        else:
            split_text = merged_text.split()
        if len(split_text) == 1 or pred.get("rejected"):
            updated_predictions.append(pred)
            continue

        current_start = start
        for text in split_text:
            str_len = len(text)
            if str_len == 0:
                current_start += 1
                continue

            split_value_start = current_start
            split_value_end = split_value_start + str_len
            current_start = split_value_end + 1
            split_val_pred_dict = {
                "text": text,
                "start": split_value_start,
                "end": split_value_end,
                "label": pred["label"],
                "confidence": pred["confidence"],
            }
            updated_predictions.append(split_val_pred_dict)
    return updated_predictions
