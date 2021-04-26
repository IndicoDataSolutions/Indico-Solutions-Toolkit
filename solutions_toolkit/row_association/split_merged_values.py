from typing import List


def split_prediction_into_many(
    prediction: dict, value_to_split_on: str = "\n"
) -> List[dict]:
    """
    Split single incorrectly merged prediction text into many based on a split value e.g. white space / line break
    Correctly updates start/end indexes, confidence of original prediction is mirrored across all 'new' predictions
    Args:
        prediction (dict): Indico extraction prediction
        value_to_split_on (str, optional): The value to split the text by. Defaults to "\n".

    Returns:
        List[dict]: A list of indico extraction predictions.If 'value_to_split_on' doesn't
                    occur in prediction, returns original prediction.
    """
    full_prediction_text = prediction["text"]
    overall_start = prediction["start"]
    split_text = full_prediction_text.split(value_to_split_on)
    split_predictions = []
    occurrence_count = {}
    for text in split_text:
        text = text.strip()
        if len(text) == 0:
            continue
        if text in occurrence_count:
            text_start_index = find_index_of_nth_string_occurrence(
                full_prediction_text, text, occurrence_count[text]
            )
            occurrence_count[text] += 1
        else:
            text_start_index = full_prediction_text.index(text)
            occurrence_count[text] = 1
        new_pred = {
            "start": overall_start + text_start_index,
            "end": overall_start + text_start_index + len(text),
            "text": text,
            "label": prediction["label"],
            "confidence": prediction["confidence"],
        }
        split_predictions.append(new_pred)
    return split_predictions


def find_index_of_nth_string_occurrence(full_string: str, sub_string: str, n: int):
    parts = full_string.split(sub_string, n + 1)
    if len(parts) <= n + 1:
        raise Exception(f"There is no {n}th occurence of {sub_string} in {full_string}")
    return len(full_string) - len(parts[-1]) - len(sub_string)
