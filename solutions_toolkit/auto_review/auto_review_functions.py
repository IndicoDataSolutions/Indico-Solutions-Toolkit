from typing import List
from collections import defaultdict


ACCEPTED = "accepted"
REJECTED = "rejected"


def empty_or_matching_label(prediction: dict, labels: list) -> bool:
    """
    Returns:
    bool: if labels list is empty or prediction label matches a label in the list
    """
    if len(labels) == 0 or prediction["label"] in labels:
        return True
    else:
        return False


def reject_by_confidence(
    predictions: List[dict], labels: List[str] = [], conf_threshold=0.50
) -> List[dict]:
    """
    Rejects predictions below a given confidence threshold
    Returns:
    predictions List[dict]: all predictions
    """
    for prediction in predictions:
        if REJECTED not in prediction:
            if not empty_or_matching_label(prediction, labels):
                continue
            if prediction["confidence"][prediction["label"]] < conf_threshold:
                prediction[REJECTED] = True
                prediction.pop(ACCEPTED, None)
    return predictions


def remove_by_confidence(
    predictions: List[dict], labels: List[str] = [], conf_threshold=0.50
) -> List[dict]:
    """
    Removes predictions below a given confidence threshold
    Returns:
    updated_predictions List[dict]: predictions above conf_threshold
    """
    for prediction in predictions:
        if REJECTED not in prediction:
            if not empty_or_matching_label(prediction, labels):
                continue
            if prediction["confidence"][prediction["label"]] < conf_threshold:
                predictions.remove(prediction)
    return predictions


def accept_by_confidence(
    predictions: List[dict], labels: List[str] = [], conf_threshold=0.98
) -> List[dict]:
    """
    Accepts predictions above a given confidence threshold
    Returns:
    predictions List[dict]: all predictions
    """
    for prediction in predictions:
        if REJECTED not in prediction:
            if not empty_or_matching_label(prediction, labels):
                continue
            if prediction["confidence"][prediction["label"]] > conf_threshold:
                prediction[ACCEPTED] = True
    return predictions


def accept_by_all_match_and_confidence(
    predictions: List[dict], labels: List[str] = [], conf_threshold=0.98
):
    """
    Accepts all predictions for a class if all their values are the same,
    and all confidence scores are above a given confidence threshold
    Returns:
    predictions List[dict]: all predictions
    """
    pred_map = defaultdict(set)
    for pred in predictions:
        if REJECTED not in pred:
            if not empty_or_matching_label(pred, labels):
                continue
            if pred["confidence"][pred["label"]] > conf_threshold:
                pred_map[pred["label"]].add(pred["text"])
            else:
                pred_map[pred["label"]].update((1, 2))
    for pred in predictions:
        if pred["label"] in pred_map:
            if len(pred_map[pred["label"]]) == 1:
                pred[ACCEPTED] = True
    return predictions


def reject_by_min_character_length(
    predictions: List[dict], labels: List[str] = [], min_length_threshold=3
) -> List[dict]:
    """
    Rejects predictions shorter than a given minimum length
    Returns:
    predictions List[dict]: all predictions
    """
    for prediction in predictions:
        if empty_or_matching_label(prediction, labels):
            if len(prediction["text"]) < min_length_threshold:
                prediction[REJECTED] = True
    return predictions


def reject_by_max_character_length(
    predictions: List[dict], labels: List[str] = [], max_length_threshold=10
) -> List[dict]:
    """
    Rejects predictions longer than a given maximum length
    Returns:
    predictions List[dict]: all prediction
    """
    for prediction in predictions:
        if empty_or_matching_label(prediction, labels):
            if len(prediction["text"]) > max_length_threshold:
                prediction[REJECTED] = True
    return predictions
