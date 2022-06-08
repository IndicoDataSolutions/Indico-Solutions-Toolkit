"""
Metrics used for evaluating and comparing partial labels models

Heavily based on:
* https://github.com/IndicoDataSolutions/finetune/blob/development/finetune/util/metrics.py
* https://github.com/IndicoDataSolutions/benchner/blob/rd/synthetic/benchner/metrics.py

For all metric calculations below:
- A "label" or "prediction" is a dictionary of the following format:
    {"start": int, "end": int, "text": str, "label": str, "doc_idx": int}
- "true" or "predicted" generally refers to a list of label dictionaries of the format above
"""
import traceback
from collections import defaultdict, OrderedDict
import copy
import functools
import random
from typing import Callable, Dict, List, Set, Tuple, Union

# Need extra packages to use these metrics
# TODO Figure out how to incorporate spacy model download into package install
try:
    import numpy as np
    import spacy
except ImportError:
    traceback.print_exc()
    raise Exception("Using partial labels requires installing additional packages")


@functools.lru_cache()
def get_spacy():
    """
    FIXME return type of spacy.lang.en.English not working for type annotation

    Load English core language model from spacy to use for tokenization. Wrapped
    with lru_cache to ensure that the model is only loaded once.

    Returns:
        nlp: Spacy model
    """
    nlp = spacy.load("en_core_web_sm", disable=["parser", "tagger", "ner", "textcat"])
    nlp.max_length = (
        800000000  # approximately one volume of the encyclopedia britannica.
    )
    return nlp


def calc_recall(num_tps: int, num_fns: int) -> float:
    """
    Calculate recall for a class given the number of true positives and false negatives

    Args:
        num_tps: Number of true positives
        num_fns: Number of false negatives

    Returns:
        recall
    """
    try:
        return num_tps / float(num_fns + num_tps)
    except ZeroDivisionError:
        return 0.0


def calc_precision(num_tps: int, num_fps: int) -> float:
    """
    Calculate precision for a class given the number of true positives and false positives

    Args:
        num_tps: Number of true positives
        num_fps: Number of false positives

    Returns:
        precision
    """
    try:
        return num_tps / float(num_fps + num_tps)
    except ZeroDivisionError:
        return 0.0


def calc_f1(recall: float, precision: float) -> float:
    """
    Calculate F1 for a class given the recall and precision

    Args:
        recall
        precision

    Returns:
        f1
    """
    try:
        return 2 * (recall * precision) / (recall + precision)
    except ZeroDivisionError:
        return 0.0


def _get_unique_classes(
    true: List[List[Dict[str, Union[int, str]]]],
    predicted: List[List[Dict[str, Union[int, str]]]],
) -> List[str]:
    """
    Given ground truth labels and predictions, take the union of label classes
    to determine the set of unique classes

    Args:
        true: Ground truth labels for a list of documents
        predicted: Model predictions for a list of documents

    Returns:
        unique_classes: A list of unique classes
    """
    true_and_pred = list(true) + list(predicted)
    return list(set([seq["label"] for seqs in true_and_pred for seq in seqs]))


def _convert_to_token_list(
    annotations: List[Dict[str, Union[int, str]]], doc_idx: int = None
) -> List[Dict[str, Union[int, str]]]:
    """
    Given annotations (labels or predictions) for a single document, use the spacy
    English tokenizer to split the annotations into individual tokens

    Args:
        annotations: Labels or predictions for a single document
        doc_idx: Document index for current document

    Returns:
        tokens
    """
    nlp = get_spacy()
    tokens = []
    annotations = copy.deepcopy(annotations)

    for annotation in annotations:
        start_idx = annotation.get("start")
        tokens.extend(
            [
                {
                    "start": start_idx + token.idx,
                    "end": start_idx + token.idx + len(token.text),
                    "text": token.text,
                    "label": annotation.get("label"),
                    "doc_idx": doc_idx,
                }
                for token in nlp(annotation.get("text"))
            ]
        )

    return tokens


def sequence_labeling_token_conf_matrix(
    true: List[List[Dict[str, Union[int, str]]]],
    predicted: List[List[Dict[str, Union[int, str]]]],
) -> Dict[str, Dict[str, List[Dict[str, Union[int, str]]]]]:
    """
    Given ground truth labels and predictions, determine the true positives (TPs),
    false positives (FPs), and false negatives (FNs) for each class at a per token level.

    Args:
        true: Ground truth labels for a list of documents
        predicted: Model predictions for a list of documents

    Returns:
        token_conf_matrix: A dictionary containing TP/FP/FN counts for each class:
            {"classA": {"true_positives": List[Dict], "false_positives": List[Dict],
                        "false_negatives": List[Dict]}, ...}
    """
    # Determine set of unique classes, and set up token_count dict for each class
    unique_classes = _get_unique_classes(true, predicted)
    token_conf_matrix = {
        cls: {"true_positives": [], "false_positives": [], "false_negatives": []}
        for cls in unique_classes
    }

    for i, (true_list, pred_list) in enumerate(zip(true, predicted)):
        # Convert span annotations to token annotations
        true_tokens = _convert_to_token_list(true_list, doc_idx=i)
        pred_tokens = _convert_to_token_list(pred_list, doc_idx=i)

        # Calculate true positives and false negatives
        for true_token in true_tokens:
            for pred_token in pred_tokens:
                if (
                    pred_token["start"] == true_token["start"]
                    and pred_token["end"] == true_token["end"]
                ):

                    if pred_token["label"] == true_token["label"]:
                        token_conf_matrix[true_token["label"]]["true_positives"].append(
                            true_token
                        )
                    else:
                        token_conf_matrix[true_token["label"]][
                            "false_negatives"
                        ].append(true_token)
                        token_conf_matrix[pred_token["label"]][
                            "false_positives"
                        ].append(pred_token)

                    break
            else:
                token_conf_matrix[true_token["label"]]["false_negatives"].append(
                    true_token
                )

        # Calculate false positives
        for pred_token in pred_tokens:
            for true_token in true_tokens:
                if (
                    pred_token["start"] == true_token["start"]
                    and pred_token["end"] == true_token["end"]
                ):
                    break
            else:
                token_conf_matrix[pred_token["label"]]["false_positives"].append(
                    pred_token
                )

    return token_conf_matrix


def sequence_labeling_conf_matrix(
    true: List[List[Dict[str, Union[int, str]]]],
    predicted: List[List[Dict[str, Union[int, str]]]],
    equality_fn: Callable[
        [Dict[str, Union[int, str]], Dict[str, Union[int, str]]], bool
    ],
) -> Dict[str, Dict[str, List[Dict[str, Union[int, str]]]]]:
    """
    Given ground truth labels and predictions, determine the true positives (TPs),
    false positives (FPs), and false negatives (FNs) for each class.

    The method to determine TPs/FPs/FNs is based on the equality function,
    and can be exact match, overlap, or superset

    Args:
        true: Ground truth labels for a list of documents
        predicted: Model predictions for a list of documents
        equality_fn: Function to determine equality between two spans

    Returns:
        conf_matrix: A dictionary containing TP/FP/FN counts for each class:
            {"classA": {"true_positives": List[Dict], "false_positives": List[Dict],
                        "false_negatives": List[Dict]}, ...}
    """
    # Determine set of unique classes, and set up count dict for each class
    unique_classes = _get_unique_classes(true, predicted)
    conf_matrix = {
        cls: {"true_positives": [], "false_positives": [], "false_negatives": []}
        for cls in unique_classes
    }

    for i, (true_annotations, predicted_annotations) in enumerate(zip(true, predicted)):
        # Add doc idx to make verification easier
        for annotations in [true_annotations, predicted_annotations]:
            for annotation in annotations:
                annotation["doc_idx"] = i

        # Calculate true positives and false negatives
        for true_annotation in true_annotations:
            for pred_annotation in predicted_annotations:
                # Use equality function to determine match between ground truth and prediction
                if equality_fn(true_annotation, pred_annotation):
                    if pred_annotation["label"] == true_annotation["label"]:
                        conf_matrix[true_annotation["label"]]["true_positives"].append(
                            true_annotation
                        )
                        break
            else:
                conf_matrix[true_annotation["label"]]["false_negatives"].append(
                    true_annotation
                )

        # Calculate false positives
        for pred_annotation in predicted_annotations:
            for true_annotation in true_annotations:
                if (
                    equality_fn(true_annotation, pred_annotation)
                    and true_annotation["label"] == pred_annotation["label"]
                ):
                    break
            else:
                conf_matrix[pred_annotation["label"]]["false_positives"].append(
                    pred_annotation
                )

    return conf_matrix


def sequences_overlap(
    true_seq: Dict[str, Union[int, str]], pred_seq: Dict[str, Union[int, str]]
) -> bool:
    """
    Determine if two annotations overlap

    Args:
        true_seq: Ground truth label
        pred_seq: Prediction

    Both true_seq and pred_seq are label dictionaries

    Returns:
        is_match: True if sequences overlap
    """
    return true_seq["start"] < pred_seq["end"] and pred_seq["start"] < true_seq["end"]


def sequence_exact_match(
    true_seq: Dict[str, Union[int, str]], pred_seq: Dict[str, Union[int, str]]
) -> bool:
    """
    Determine if two annotations are an exact match (with stripped whitespace)

    Args:
        true_seq: Ground truth label
        pred_seq: Prediction

    Both true_seq and pred_seq are label dictionaries

    Returns:
        is_match: True if sequences are an exact match
    """
    true_seq = strip_whitespace(true_seq)
    pred_seq = strip_whitespace(pred_seq)
    return pred_seq["start"] == true_seq["start"] and pred_seq["end"] == true_seq["end"]


def sequence_superset(
    true_seq: Dict[str, Union[int, str]], pred_seq: Dict[str, Union[int, str]]
) -> bool:
    """
    Given a ground truth label and a prediction, determine if the prediction is
    a superset of the ground truth label (with stripped whitespace)

    Args:
        true_seq: Ground truth label
        pred_seq: Prediction

    Both true_seq and pred_seq are label dictionaries

    Returns:
        is_match: True if pred_seq is a superset of true_seq
    """
    true_seq = strip_whitespace(true_seq)
    pred_seq = strip_whitespace(pred_seq)
    return pred_seq["start"] <= true_seq["start"] and pred_seq["end"] >= true_seq["end"]


def get_seq_conf_matrix_fn(
    span_type: str = "token",
) -> Callable[
    [List[List[Dict[str, Union[int, str]]]], List[List[Dict[str, Union[int, str]]]]],
    Dict[str, Dict[str, List[Dict[str, Union[int, str]]]]],
]:
    """
    Determine what function to use for determining TPs/FPs/FNs based on the
    type of equality function to use.

    Args:
        span_type: Type of "span" to use to determine the equality function
            to use. Must be one of {"token", "equality", "partial", "overlap"}

    Returns:
        seq_conf_matrix_fn: Function to determine TPs/FPs/FNs
    """
    valid_span_types = {"token", "equality", "partial", "overlap"}
    if span_type not in valid_span_types:
        raise ValueError(
            f"span_type={span_type} is not valid, must be within {valid_span_types}"
        )

    span_type_fn_mapping = {
        "token": sequence_labeling_token_conf_matrix,
        "overlap": functools.partial(
            sequence_labeling_conf_matrix, equality_fn=sequences_overlap
        ),
        "exact": functools.partial(
            sequence_labeling_conf_matrix, equality_fn=sequence_exact_match
        ),
        "superset": functools.partial(
            sequence_labeling_conf_matrix, equality_fn=sequence_superset
        ),
    }
    return span_type_fn_mapping[span_type]


def strip_whitespace(
    annotation: Dict[str, Union[int, str]]
) -> Dict[str, Union[int, str]]:
    """
    Given a label annotation, strip whitespace from the start and end of the
    string and adjust the start/end indices of the annotation

    Args:
        annotation: Label annotation

    Returns:
        new_annotation: Updated annotation with stripped whitespace
    """
    label_text = annotation["text"]
    lstripped = label_text.lstrip()
    new_start = annotation["start"] + (len(label_text) - len(lstripped))
    stripped = label_text.strip()
    return {
        "text": label_text.strip(),
        "start": new_start,
        "end": new_start + len(stripped),
        "label": annotation["label"],
    }


def seq_recall(
    true: List[List[Dict[str, Union[int, str]]]],
    predicted: List[List[Dict[str, Union[int, str]]]],
    span_type: str = "token",
) -> Dict[str, float]:
    """
    Given ground truth labels and predictions, determine the recall for
    each class

    The method to determine TPs/FPs/FNs is based on the span type, which
    determines the equality function to compare ground truth and preds

    Args:
        true: Ground truth labels for a list of documents
        predicted: Model predictions for a list of documents
        span_type: Type of "span" to use to determine the equality function
            to use. Must be one of {"token", "equality", "partial", "overlap"}

    Returns:
        recalls: Recall for each class
    """
    valid_span_types = {"token", "equality", "partial", "overlap"}
    if span_type not in valid_span_types:
        raise ValueError(
            f"span_type={span_type} is not valid, must be within {valid_span_types}"
        )

    conf_matrix_fn = get_seq_conf_matrix_fn(span_type)
    # Get counts of TP/FP/FN for each class
    class_conf_matrices = conf_matrix_fn(true, predicted)
    recalls = {}
    for cls, conf_matrix in class_conf_matrices.items():
        num_tps = len(conf_matrix["true_positives"])
        num_fns = len(conf_matrix["false_negatives"])
        recalls[cls] = calc_recall(num_tps, num_fns)
    return recalls


def seq_precision(
    true: List[List[Dict[str, Union[int, str]]]],
    predicted: List[List[Dict[str, Union[int, str]]]],
    span_type: str = "token",
) -> Dict[str, float]:
    """
    Given ground truth labels and predictions, determine the precision for
    each class

    The method to determine TPs/FPs/FNs is based on the span type, which
    determines the equality function to compare ground truth and preds

    Args:
        true: Ground truth labels for a list of documents
        predicted: Model predictions for a list of documents
        span_type: Type of "span" to use to determine the equality function
            to use. Must be one of {"token", "equality", "partial", "overlap"}

    Returns:
        precisions: Precision for each class
    """
    valid_span_types = {"token", "equality", "partial", "overlap"}
    if span_type not in valid_span_types:
        raise ValueError(
            f"span_type={span_type} is not valid, must be within {valid_span_types}"
        )

    conf_matrix_fn = get_seq_conf_matrix_fn(span_type)
    # Get counts of TP/FP/FN for each class
    class_conf_matrices = conf_matrix_fn(true, predicted)
    precisions = {}
    for cls, conf_matrix in class_conf_matrices.items():
        num_tps = len(conf_matrix["true_positives"])
        num_fps = len(conf_matrix["false_positives"])
        precisions[cls] = calc_recall(num_tps, num_fps)
    return precisions


def calc_micro_f1(
    true: List[List[Dict[str, Union[int, str]]]],
    predicted: List[List[Dict[str, Union[int, str]]]],
    span_type: str = "token",
    include_recall_and_precision: bool = False,
) -> Union[Tuple[float, float, float], float]:
    """
    Given ground truth labels and predictions, determine the micro F1 score.
    Micro means calculating metrics globally by counting the total true positives,
    false negatives and false positives.

    Args:
        true: Ground truth labels for a list of documents
        predicted: Model predictions for a list of documents
        span_type: Type of "span" to use to determine the equality function
            to use. Must be one of {"token", "equality", "partial", "overlap"}
        include_recall_and_precision: If True, return a Tuple including the micro
            recall, precision, and F1. Else just return F1

    Returns:
        If include_recall_and_precision is True:
            recall
            precision
            f1
        Else:
            f1
    """
    conf_matrix_fn = get_seq_conf_matrix_fn(span_type)
    class_conf_matrices = conf_matrix_fn(true, predicted)
    true_positives, false_positives, false_negatives = 0, 0, 0
    for _, conf_matrix in class_conf_matrices.items():
        false_negatives += len(conf_matrix["false_negatives"])
        true_positives += len(conf_matrix["true_positives"])
        false_positives += len(conf_matrix["false_positives"])
    recall = calc_recall(true_positives, false_negatives)
    precision = calc_precision(true_positives, false_positives)
    f1 = calc_f1(recall, precision)
    if include_recall_and_precision:
        return recall, precision, f1
    return f1


def calc_per_class_f1(
    true: List[List[Dict[str, Union[int, str]]]],
    predicted: List[List[Dict[str, Union[int, str]]]],
    span_type: str = "token",
) -> Dict[str, Dict[str, Union[float, int]]]:
    """
    Given ground truth labels and predictions, determine the support (TPs+FNs)
    and F1 score for each class.

    Args:
        true: Ground truth labels for a list of documents
        predicted: Model predictions for a list of documents
        span_type: Type of "span" to use to determine the equality function
            to use. Must be one of {"token", "equality", "partial", "overlap"}

    Returns:
        results: OrderedDict containing support (TPs + FNs) and F1 score per class
            Note: Using Dict in return val type annotation to prevent TypeError
    """
    conf_matrix_fn = get_seq_conf_matrix_fn(span_type)
    class_conf_matrices = conf_matrix_fn(true, predicted)
    results = OrderedDict()
    for cls, conf_matrix in class_conf_matrices.items():
        results[cls] = {}
        num_tps = len(conf_matrix["true_positives"])
        num_fps = len(conf_matrix["false_positives"])
        num_fns = len(conf_matrix["false_negatives"])
        # Calculate per class precision and recall, and then F1
        recall = calc_recall(num_tps, num_fns)
        precision = calc_precision(num_tps, num_fps)
        results[cls]["support"] = num_tps + num_fns
        results[cls]["f1_score"] = calc_f1(recall, precision)
    return results


def calc_sequence_f1(
    true: List[List[Dict[str, Union[int, str]]]],
    predicted: List[List[Dict[str, Union[int, str]]]],
    span_type: str = "token",
    average: str = None,
) -> Union[float, Dict[str, Dict[str, Union[float, int]]]]:
    """
    Given ground truth labels and predictions, determine F1 score. The F1
    score can be calculated in different ways depending on the average
    parameter, which could be "micro", "macro", or "weighted" to calculate
    a single float value.

    If average is None, instead calculate per class F1 scores

    If average = None, return per-class F1 scores, otherwise
    return the requested model-level score.

    Args:
        true: Ground truth labels for a list of documents
        predicted: Model predictions for a list of documents
        span_type: Type of "span" to use to determine the equality function
            to use. Must be one of {"token", "equality", "partial", "overlap"}
        average: Metric to use to calculate F1. This is explained further in sklearn:
            https://scikit-learn.org/stable/modules/generated/sklearn.metrics.f1_score.html

    Returns:
        f1: F1 score in float form if average is "micro", "macro", or "weighted".
            Otherwise an OrderedDict with per class F1 scores
    """
    if average == "micro":
        return calc_micro_f1(true, predicted, span_type)

    f1s_by_class = calc_per_class_f1(true, predicted, span_type)
    f1s = [value.get("f1_score") for key, value in f1s_by_class.items()]
    supports = [value.get("support") for key, value in f1s_by_class.items()]

    if average == "weighted":
        return np.average(np.array(f1s), weights=np.array(supports))
    if average == "macro":
        return np.average(f1s)
    else:
        return f1s_by_class


################################################################
# All metrics below are not based on existing finetune metrics #
################################################################


def find_overlapping_sequence(
    pred: Dict[str, Union[int, str]], labels: List[Dict[str, Union[int, str]]]
) -> Union[Dict[str, Union[int, str]], None]:
    """
    Given a prediction and a set of ground truth labels, find the label sequence
    that overlaps with the prediction.

    Return None if no sequence is found

    Args:
        pred: Individual prediction (label dictionary)
        labels: List of ground truth label dictionaries for a document

    Returns:
        overlapping_label
    """
    for label in labels:
        if sequences_overlap(pred, label):
            return label

    return None


def identify_tps_fps_fns(
    true: List[List[Dict[str, Union[int, str]]]],
    predicted: List[List[Dict[str, Union[int, str]]]],
    tp_ratio: float = 1,
    fp_ratio: float = 1,
    fn_ratio: float = 1,
    random_seed: int = 42,
    tp_match_type: str = "exact",
    fp_match_type: str = "overlap",
    fn_match_type: str = "exact",
    replace_fps: bool = False,
    missing_label_ratio: float = None,
) -> Tuple[
    List[List[Dict[str, Union[int, str]]]],
    List[List[Dict[str, Union[int, str]]]],
    List[List[Dict[str, Union[int, str]]]],
]:
    """
    Given ground truth labels and predictions for a sequence labeling model,
    we want to identify the true positives, false positives, and false negatives.
    If any of the ratios (tp_ratio/fp_ratio/fn_ratio) are left at the defaults (0),
    we return an empty list. If the ratio is a float between 0 and 1, we sample
    that ratio of TPs, FPs, or FNs.

    The sequence_labeling_counts already identifies true positives, false positives,
    and false negatives, but in a significantly different format from what is expected by finetune.
    The format coming out of sequence_labeling_counts() is as follows:
    {
        <LABEL>: {
            "true_positives": int,
            "false_positives": int,
            "false_negatives": int
        },
        ...
    }

    The format expected by finetune is as follows, where annotations are separated
    for each document, and NOT separated by the different labels:
    [
        # Document 0
        [
            {
                "start": int, "end": int, "text": str, "label": str, "doc_idx": 0,
                "type": OneOf("tp", "fp", "fn")
            },
            ...
        ],
        # Document 1
        [...],
        ...
    ]

    Args:
        true: List of lists, where each sublist contains ground truth annotations
            for a given document
        predicted: List of lists, where each sublist contains predictions for a given document
        tp_ratio: Ratio of true positives to include, sampled randomly across all documents
        fp_ratio: Ratio of false positives to include, sampled randomly across all documents
        fn_ratio: Ratio of false negatives to include, sampled randomly across all documents
        random_seed: Random seed to use when sampling
        tp_match_type: Type of match in finetune metrics to use for identifying true positives.
            Must be one of ("exact", "overlap")
        fp_match_type: Same as above, but for false positives
        fn_match_type: Same as above, but for false negatives
        replace_fps: If we replace false positives with overlapping ground truth
            Very strong supervision, because we're relying on the reviewer or labeler
            to tell us the class and start/end of the overlapping ground truth
        missing_label_ratio: Used for simulating missing label classes for experiments.
            A ratio of X means that we will keep (1 - X) ratio of classes

    Returns:
        tps: List of lists, where each "sublist" includes all true positive
            annotations from a document
        fps: List of lists, where each "sublist" includes all false positive
            annotations from a document
        fns: List of lists, where each "sublist" includes all false negative
            annotations from a document
    """
    # Validate inputs
    if tp_ratio and tp_match_type not in {"exact", "overlap"}:
        raise ValueError(
            f"tp_match_type={tp_match_type} not allowed. Must be one of ('exact', 'overlap')"
        )
    if fp_ratio and fp_match_type not in {"exact", "overlap"}:
        raise ValueError(
            f"fp_match_type={fp_match_type} not allowed. Must be one of ('exact', 'overlap')"
        )
    if fn_ratio and fn_match_type not in {"exact", "overlap"}:
        raise ValueError(
            f"fn_match_type={fn_match_type} not allowed. Must be one of ('exact', 'overlap')"
        )

    equality_slc_map = {
        "exact": sequence_labeling_conf_matrix(true, predicted, sequence_exact_match),
        "overlap": sequence_labeling_conf_matrix(true, predicted, sequences_overlap),
    }

    # Get true positives and false positives in the format returned by sequence_labeling_conf_matrix
    slc_tp = equality_slc_map[tp_match_type] if tp_ratio else {}
    slc_fp = equality_slc_map[fp_match_type] if fp_ratio else {}
    slc_fn = equality_slc_map[fn_match_type] if fn_ratio else {}

    label_classes = set(list(slc_fp.keys()) + list(slc_fp.keys()) + list(slc_fn.keys()))
    # Sample labels to keep only a subset of classes if missing_label_ratio is present
    if missing_label_ratio:
        random.seed(random_seed)
        label_classes = random.sample(
            label_classes, int(len(label_classes) * (1 - missing_label_ratio))
        )

    flat_tps, flat_fps, flat_fns, = (
        [],
        [],
        [],
    )
    for label in label_classes:
        if label in slc_tp:
            flat_tps.extend(slc_tp[label]["true_positives"])
        # Sometimes we see predictions with identical start and end indices
        # It does not make sense to label these sequences since they don't
        # span any text, so skip them
        if label in slc_fp:
            flat_fps.extend(
                fp
                for fp in slc_fp[label]["false_positives"]
                if fp["start"] != fp["end"]
            )
        if label in slc_fn:
            flat_fns.extend(slc_fn[label]["false_negatives"])

    # Sample from flattened list(s)
    # Don't need to sample if ratio is 1
    # If ratio is 0, set flat_XXs back to an empty list
    if not tp_ratio:
        flat_tps = []
    elif tp_ratio != 1:
        num_samples = int(tp_ratio * len(flat_tps))
        random.seed(random_seed)
        flat_tps = random.sample(flat_tps, num_samples)

    if not fp_ratio:
        flat_fps = []
    elif fp_ratio != 1:
        num_samples = int(fp_ratio * len(flat_fps))
        random.seed(random_seed)
        flat_fps = random.sample(flat_fps, num_samples)

    if not fn_ratio:
        flat_fns = []
    elif fn_ratio != 1:
        num_samples = int(fn_ratio * len(flat_fns))
        random.seed(random_seed)
        flat_fns = random.sample(flat_fns, num_samples)

    # tps, fps, and fns should contain len(true) number of lists
    tps = [[] for _ in range(len(true))]
    fps = [[] for _ in range(len(true))]
    fns = [[] for _ in range(len(true))]

    for tp in flat_tps:
        tp["type"] = "tp"
        idx = tp["doc_idx"]
        tps[idx].append(tp)

    for fp in flat_fps:
        fp["orig_label"] = fp["label"]
        if not replace_fps:
            # This is flawed, because treating false positives as <PAD> sequences
            # may cause problems if the sequence actually is label A, but was
            # predicted as label B. In this case, we would be teaching the model the
            # incorrect behavior
            fp["label"] = "<PAD>"
        fp["type"] = "fp"
        idx = fp["doc_idx"]
        fps[idx].append(fp)

    for fn in flat_fns:
        fn["type"] = "fn"
        idx = fn["doc_idx"]
        fns[idx].append(fn)

    return tps, fps, fns


###################
# Complex metrics #
###################


def alphanumeric_lower(label_text: str) -> str:
    """
    Given text for a label, return lowercase alphanumeric characters

    Args:
        label_text

    Returns:
        label_text
    """
    return "".join(char for char in label_text if char.isalnum()).lower()


def find_many_match(
    label: Dict[str, Union[int, str]], preds: List[Dict[str, Union[int, str]]]
) -> Union[Dict[str, Union[int, str]], None]:
    """
    Check if any prediction matches with label based on checking for an
    alphanumeric lowercase string match.

    Each prediction can only match with one label (and vice versa), so
    this requires the prediction match candidate to not already be matched
    to a label.

    Returns None if there is no match

    Args:
        label: Ground truth label
        preds: List of predictions

    Returns:
        pred: Matched prediction
    """
    for pred in preds:
        if (
            alphanumeric_lower(label["text"]) == alphanumeric_lower(pred["text"])
        ) and not pred["matched"]:
            return pred

    return None


def many_conf_matrix(
    labels: List[Dict[str, Union[int, str]]], preds: List[Dict[str, Union[int, str]]]
) -> Tuple[int, int, int]:
    """
    Given ground truth labels and predictions for a given class of a document,
    compute the confusion matrix

    Args:
        labels: Labels for a document
        preds: Predictions for a document

    Returns:
        num_tps: Number of true positives for that class and document
        num_fps: : Number of false positives for that class and document
        num_fns: Number of false negatives for that class and document
    """
    # Initialize match values to False
    for label in labels:
        label["matched"] = False
    for pred in preds:
        pred["matched"] = False

    for label in labels:
        pred_match = find_many_match(label, preds)
        if pred_match:
            label["matched"] = True
            pred_match["matched"] = True

    num_tps = sum(int(label["matched"]) for label in labels)
    num_fns = sum(int(not label["matched"]) for label in labels)
    num_fps = sum(int(not pred["matched"]) for pred in preds)
    return num_tps, num_fns, num_fps


def calc_macro_metric(
    one_metric: Dict[str, float], many_metric: Dict[str, float] = {}
) -> float:
    """
    Given per class metrics for recall, precision, or F1, for both classes
    that appear once or many times per doc, take the mean of the classes to
    return a macro metric.

    Args:
        one_metric: Per class recall, precision, or F1 for labels that should
            appear max once per doc
        many_metric: Same as above, but for labels that appear many times per doc

    Returns:
        macro_metric: Macro average of recall, precision, or F1
    """

    return np.array(list(one_metric.values()) + list(many_metric.values())).mean()


def calc_micro_metric(
    one_metric: Dict[str, float],
    one_counts: Dict[str, Dict[str, int]],
    many_metric: Dict[str, float] = None,
    many_counts: Dict[str, Dict[str, int]] = None,
) -> float:
    """
    Given per class metrics for recall, precision, or F1, for both classes
    that appear once or many times per doc, use the also provided counts
    for each class to compute a weighted average that weights each class
    based on the amount of support it has.

    Args:
        one_metric: Per class recall, precision, or F1 for labels that should
            appear max once per doc
        one_counts: Per class support for one_metric labels for weighting
        many_metric: Same as one_metric, but for labels that appear many times per doc
        many_counts: Per class support for many_metric labels for weighting

    Returns:
        micro_metric: Micro average of recall, precision, or F1
    """
    metric_sum = 0
    metric_counts = 0
    for cls in one_metric:
        cls_count = one_counts[cls]["tp"] + one_counts[cls]["fn"]
        metric_sum += one_metric[cls] * cls_count
        metric_counts += cls_count
    if many_metric:
        for cls in many_metric:
            cls_count = many_counts[cls]["tp"] + many_counts[cls]["fn"]
            metric_sum += many_metric[cls] * cls_count
            metric_counts += cls_count
    return metric_sum / metric_counts


def seq_recall_precision_f1(
    true: List[List[Dict[str, Union[int, str]]]],
    predicted: List[List[Dict[str, Union[int, str]]]],
    span_type: str = "token",
) -> Tuple[
    Dict[str, float], Dict[str, float], Dict[str, float], Dict[str, Dict[str, int]]
]:
    """
    Given true and predicted labels, calculate per class precision,
    recall, F1, and and support

    Args:
        true: Sequence labeling labels for each document
        predicted: Model predictions for labels for each doc
        span_type: How to determine matches between true and prediction.
            Valid options are "token", "overlap", "exact", and "superset"

    Returns:
        recall: Per class recall
        precision: Per class precision
        f1: Per class F1
        support: FP, FN, and TP counts per class
    """
    conf_matrix_fn = get_seq_conf_matrix_fn(span_type)
    class_conf_matrices = conf_matrix_fn(true, predicted)
    recall = {}
    precision = {}
    f1 = {}
    support = {}
    for cls, conf_matrix in class_conf_matrices.items():
        num_fns = len(conf_matrix["false_negatives"])
        num_fps = len(conf_matrix["false_positives"])
        num_tps = len(conf_matrix["true_positives"])
        # Skip classes with no support
        if num_fns + num_fps + num_tps == 0:
            continue
        recall[cls] = calc_recall(num_tps, num_fns)
        precision[cls] = calc_precision(num_tps, num_fps)
        f1[cls] = calc_f1(recall[cls], precision[cls])
        support[cls] = {"fp": num_fps, "fn": num_fns, "tp": num_tps}

    return recall, precision, f1, support


def find_best_label(
    label_cls: str,
    label_candidates: List[Dict[str, Union[int, str]]],
    doc_fns: List[Dict[str, Union[int, str]]],
) -> str:
    """
    Helper function for dedup_test_labels() that is called per label per document
    any time there are multiple labels of a class that should only appear once
    per document.

    Args:
        label_cls: Name of target label class
        label_candidates: Labels of the target label class
        doc_fns: All false negatives for the current document

    Returns:
        text: Text for the chosen best label
    """
    # First try to find false negative
    for fn in doc_fns:
        if fn["label"] == label_cls:
            return fn["text"]
    # If no false negatives, default to first label
    sorted_cands = sorted(label_candidates, key=lambda x: x["start"])
    return sorted_cands[0]["text"]


def dedup_test_labels(
    doc_labels: Dict[str, List[Dict[str, Union[int, str]]]],
    doc_fns: List[Dict[str, Union[int, str]]],
) -> Dict[str, str]:
    """
    For classes that should only appear once per document, we need a way
    to choose the "best" label from review data in the case of duplicates.
    The methodology for doing so is as follows.

    1. If there are any false negatives for this class, choose the first
        one (by start index)
    2. Else, use the first value in the review set (by start index)

    Args:
        doc_labels: Dictionary with a list per label class with
            candidates for that label
        doc_fns: List of all false negatives for a doc

    Returns:
        deduped_labels: Dictionary with the best label for each class
    """
    deduped_labels = {}
    doc_fns = sorted(doc_fns, key=lambda x: x["start"])
    for label_cls, labels in doc_labels.items():
        if len(labels) == 1:
            deduped_labels[label_cls] = labels[0]["text"]
        else:
            deduped_labels[label_cls] = find_best_label(label_cls, labels, doc_fns)
    return deduped_labels


def run_evaluation(
    test_preds: List[List[Dict[str, Union[int, str]]]],
    test_labels: List[List[Dict[str, Union[int, str]]]],
    one_classes: Set[str],
    verbose: bool = False,
) -> Dict[str, float]:
    """
    Complex evaluation methodology to treat labels separately depending on if they
    should appear at most once per document or several times. This methodology
    assumes that we are using review data for our test set.
    \
    1. Separate test preds into one vs many
    2. For one, process down to a single value (no indices) based on the
        highest confidence prediction
    3. Separate test labels into one vs many
    4. Get FNs b/w test preds and labels
    5. For one, process down to max one label per document in this order:
        a) If there are any false negatives, choose the first one (by start index)
        b) Use the first value in the labels (by start index)
    6. Use existing metrics calculations to get per class precision and recall
        on "many" preds vs labels
    7. Use string matching (only alphanumeric chars, all lowercase) to determine
        TPs, FPs, and FNs for "one" preds vs labels
    8. Calculate precision and recall on "one" classes
    9. Calculate macro metrics
    10. Calculate micro metrics

    Args:
        test_preds: Predictions on the test set for each document
        test_labels: Labels on the test set for each document
        one_classes: Set of class names that should appear max once per doc
        verbose: If True, print more detailed recall/precision/F1 statistics
    """
    # 1. Separate test preds into one vs many
    # 2. For one, process down to a single value (no indices) based on the
    # highest confidence prediction
    # Note that test_preds_one is a list of dictionaries (one entry per label
    # per doc) while test_preds_many is a list of lists
    test_preds_one = []
    test_preds_many = []
    for doc_preds in test_preds:
        doc_preds_one = {}
        doc_preds_many = []
        for pred in doc_preds:
            label = pred["label"]
            if label in one_classes:
                if label in doc_preds_one:
                    # Replace existing pred in doc_preds_one if the confidence
                    # of the current pred is higher
                    conf = pred["confidence"][label]
                    if conf > doc_preds_one[label]["conf"]:
                        doc_preds_one[label] = {"text": pred["text"], "conf": conf}
                else:
                    doc_preds_one[label] = {
                        "text": pred["text"],
                        "conf": pred["confidence"][label],
                    }
            else:
                doc_preds_many.append(pred)
        test_preds_one.append(doc_preds_one)
        test_preds_many.append(doc_preds_many)

    # 3. Separate test labels into one vs many
    test_labels_one_w_dups = []
    test_labels_many = []
    for doc_labels in test_labels:
        doc_label_candidates_one = {}
        doc_labels_many = []
        for label in doc_labels:
            if label["label"] in one_classes:
                if label["label"] in doc_label_candidates_one:
                    doc_label_candidates_one[label["label"]].append(label)
                else:
                    doc_label_candidates_one[label["label"]] = [label]
            else:
                doc_labels_many.append(label)
        test_labels_one_w_dups.append(doc_label_candidates_one)
        test_labels_many.append(doc_labels_many)

    # 4. Get FNs between test preds and labels
    _, _, test_fns = identify_tps_fps_fns(
        true=test_labels,
        predicted=test_preds,
        tp_ratio=0,
        fp_ratio=0,
        fn_ratio=1,
    )

    # 5. For "one", process down to max one label per document
    test_labels_one = []
    for doc_labels, doc_fns in zip(test_labels_one_w_dups, test_fns):
        test_labels_one.append(dedup_test_labels(doc_labels, doc_fns))

    # 6. Use existing metrics calculations to get per class precision and recall
    # on "many" preds vs labels
    many_recall, many_precision, many_f1, many_counts = seq_recall_precision_f1(
        test_labels_many, test_preds_many
    )

    # 7. Use string matching (only alphanumeric chars, all lowercase) to determine
    # TPs, FPs, and FNs for "one" preds vs labels
    cm_counts_one = {cls: defaultdict(int) for cls in one_classes}
    for doc_preds, doc_labels in zip(test_preds_one, test_labels_one):
        for cls in one_classes:
            pred_text = doc_preds.get(cls, {}).get("text")
            label_text = doc_labels.get(cls, {}).get("text")
            if pred_text is not None and label_text is None:
                cm_counts_one[cls]["fp"] += 1
            elif label_text is not None and pred_text is None:
                cm_counts_one[cls]["fn"] += 1
            elif pred_text is not None and label_text is not None:
                # Process pred and label to lowercase alphanumeric chars for comparison
                pred = alphanumeric_lower(pred_text)
                label = alphanumeric_lower(label_text)
                if pred == label:
                    cm_counts_one[cls]["tp"] += 1
                else:
                    cm_counts_one[cls]["fp"] += 1
                    cm_counts_one[cls]["fn"] += 1

    # 8. Calculate precision and recall on "one" classes
    one_recall = {}
    one_precision = {}
    one_f1 = {}
    for cls, counts in cm_counts_one.items():
        # Skip classes with no support if that happens for any reason
        if counts["tp"] + counts["fp"] + counts["fn"] > 0:
            one_recall[cls] = calc_recall(counts["tp"], counts["fn"])
            one_precision[cls] = calc_precision(counts["tp"], counts["fp"])
            one_f1[cls] = calc_f1(one_recall[cls], one_precision[cls])

    # 9. Macro metrics
    macro_recall = calc_macro_metric(one_recall, many_recall)
    macro_precision = calc_macro_metric(one_precision, many_precision)
    macro_f1 = calc_macro_metric(one_f1, many_f1)

    # 10. Micro metrics
    micro_recall = calc_micro_metric(
        one_recall, cm_counts_one, many_recall, many_counts
    )
    micro_precision = calc_micro_metric(
        one_precision, cm_counts_one, many_precision, many_counts
    )
    micro_f1 = calc_micro_metric(one_f1, cm_counts_one, many_f1, many_counts)

    if verbose:
        print("One recall", one_recall)
        print("One precision", one_precision)
        print("One f1", one_f1)
        print("One support", cm_counts_one)
        print("Many recall", many_recall)
        print("Many precision", many_precision)
        print("Many f1", many_f1)
        print("Many support", many_counts)

    final_metrics = {
        "macro_recall": macro_recall,
        "macro_precision": macro_precision,
        "macro_f1": macro_f1,
        "micro_recall": micro_recall,
        "micro_precision": micro_precision,
        "micro_f1": micro_f1,
    }
    return final_metrics


def eval_value_matching(
    test_preds: List[List[Dict[str, Union[int, str]]]],
    test_labels: List[List[Dict[str, Union[int, str]]]],
    one_classes: Set[str],
    all_classes: Set[str],
    verbose: bool = False,
) -> Dict[str, float]:
    """
    Complex evaluation methodology to treat labels separately depending on if they
    should appear at most once per document or several times.

    This function is identical to run_evaluation(), except that for this comparison,
    we compare values directly instead of using start/end indices.

    1. Separate test preds into one vs many
    2. For one, process down to a single value (no indices) based on the
        highest confidence prediction
    3. Separate test labels into one vs many
    4. Get FNs between test preds and labels by doing string matches
    5. For "one", process each class down to a set of labels using the following logic:
        a) If there are any false negatives, create a set of them
        b) Else, create a set of all of the labels of that class
    6. For "many" preds vs labels, use string matching (only alphanumeric chars,
        all lowercase) to get TPs, FPs, and FNs
    7. Calculate precision and recall on "many" classes
    8. Apply the same string matching technique to "one" preds vs labels
    9. Calculate precision and recall on "one" classes
    10. Calculate micro metrics
    11. Calculate macro metrics

    Args:
        test_preds: Predictions on the test set for each document
        test_labels: Labels on the test set for each document
        one_classes: Set of class names that should appear max once per doc
        all_classes: Set of all classes that can appear for this workflow
        verbose: If True, print more detailed recall/precision/F1 statistics

    Returns:
        eval_metrics: Micro and macro precision, recall, and F1
    """
    # 1. Separate test preds into one vs many
    # 2. For one, process down to a single value (no indices) for each class
    # based on the highest confidence prediction
    # For many, process down to a list of labels for each class
    test_preds_one = []
    test_preds_many = []
    for doc_preds in test_preds:
        doc_preds_one = {}
        doc_preds_many = defaultdict(list)
        for pred in doc_preds:
            label = pred["label"]
            if label in one_classes:
                if label in doc_preds_one:
                    # Replace existing pred in doc_preds_one if the confidence
                    # of the current pred is higher
                    conf = pred["confidence"][label]
                    if conf > doc_preds_one[label]["conf"]:
                        doc_preds_one[label] = {"text": pred["text"], "conf": conf}
                else:
                    doc_preds_one[label] = {
                        "text": pred["text"],
                        "conf": pred["confidence"][label],
                    }
            else:
                doc_preds_many[label].append(pred)
        test_preds_one.append(doc_preds_one)
        test_preds_many.append(doc_preds_many)

    # 3. Separate test labels into one vs many
    # "one" has a set for each class for each doc. Each element of the set
    #   is just alphanumeric lowercase text
    # "many" has a list of the full label dicts for each class in each doc
    test_labels_one_w_dups = []
    test_labels_many = []
    for doc_labels in test_labels:
        doc_label_candidates_one = defaultdict(set)
        doc_labels_many = defaultdict(list)
        for label in doc_labels:
            if label["label"] in one_classes:
                doc_label_candidates_one[label["label"]].add(
                    alphanumeric_lower(label["text"])
                )
            else:
                doc_labels_many[label["label"]].append(label)
        test_labels_one_w_dups.append(doc_label_candidates_one)
        test_labels_many.append(doc_labels_many)

    # 4. Get FNs between test preds and labels by doing string matches
    # Each element of test_fns is a defaultdict from label class name
    # to a set of the false negatives for the label in the current doc
    test_fns = []
    for doc_labels, doc_preds in zip(test_labels, test_preds):
        doc_fns = defaultdict(set)
        doc_pred_strs = set(alphanumeric_lower(pred["text"]) for pred in doc_preds)
        for label in doc_labels:
            label_str = alphanumeric_lower(label["text"])
            # If this condition is met, label is a false negative
            if label_str not in doc_pred_strs:
                doc_fns[label["label"]].add(label_str)
        test_fns.append(doc_fns)

    # 5. For "one", process each class down to a set of labels using the following logic:
    #   a) If there are any false negatives, create a set of them
    #   b) Else, create a set of all of the labels of that class
    test_labels_one = []
    for doc_labels, doc_fns in zip(test_labels_one_w_dups, test_fns):
        doc_labels_one = {}
        for cls in one_classes:
            if doc_fns.get(cls):
                doc_labels_one[cls] = doc_fns[cls]
            elif doc_labels_one.get(cls):
                doc_labels_one[cls] = doc_labels[cls]
        test_labels_one.append(doc_labels_one)

    # 6. For "many" preds vs labels, use string matching (only alphanumeric chars,
    # all lowercase) to get TPs, FPs, and FNs
    many_classes = all_classes - one_classes
    cm_counts_many = {cls: defaultdict(int) for cls in many_classes}
    for doc_preds, doc_labels in zip(test_preds_many, test_labels_many):
        for cls in many_classes:
            tps, fps, fns = many_conf_matrix(
                doc_labels.get(cls, []), doc_preds.get(cls, [])
            )
            cm_counts_many[cls]["tp"] += tps
            cm_counts_many[cls]["fp"] += fps
            cm_counts_many[cls]["fn"] += fns

    # 7. Calculate precision and recall on "many" classes
    many_recall = {}
    many_precision = {}
    many_f1 = {}
    for cls, counts in cm_counts_many.items():
        # Skip classes with no support if that happens for any reason
        if counts["tp"] + counts["fp"] + counts["fn"] > 0:
            many_recall[cls] = calc_recall(counts["tp"], counts["fn"])
            many_precision[cls] = calc_precision(counts["tp"], counts["fp"])
            many_f1[cls] = calc_f1(many_recall[cls], many_precision[cls])

    # 8. Use string matching (only alphanumeric chars, all lowercase) to determine
    # TPs, FPs, and FNs for "one" preds vs labels
    cm_counts_one = {cls: defaultdict(int) for cls in one_classes}
    for doc_preds, doc_labels in zip(test_preds_one, test_labels_one):
        for cls in one_classes:
            pred = doc_preds.get(cls)
            labels = doc_labels.get(cls, {})
            if pred is not None and labels == {}:
                cm_counts_one[cls]["fp"] += 1
            elif pred is None and labels != {}:
                cm_counts_one[cls]["fn"] += 1
            elif pred is not None and labels != {}:
                # Check if pred is in the set of labels or not
                if alphanumeric_lower(pred["text"]) in labels:
                    cm_counts_one[cls]["tp"] += 1
                # Even if the set of labels has multiple "wrong" labels, we only
                # treat it as a single error, because ideally we would have a
                # constraint in place to only have a single prediction for labels
                # that should appear max once per document
                else:
                    cm_counts_one[cls]["fp"] += 1
                    cm_counts_one[cls]["fn"] += 1

    # 9. Calculate precision and recall on "one" classes
    one_recall = {}
    one_precision = {}
    one_f1 = {}
    for cls, counts in cm_counts_one.items():
        # Skip classes with no support if that happens for any reason
        if counts["tp"] + counts["fp"] + counts["fn"] > 0:
            one_recall[cls] = calc_recall(counts["tp"], counts["fn"])
            one_precision[cls] = calc_precision(counts["tp"], counts["fp"])
            one_f1[cls] = calc_f1(one_recall[cls], one_precision[cls])

    # 10. Macro metrics
    macro_recall = calc_macro_metric(one_recall, many_recall)
    macro_precision = calc_macro_metric(one_precision, many_precision)
    macro_f1 = calc_macro_metric(one_f1, many_f1)

    # 11. Micro metrics
    micro_recall = calc_micro_metric(
        one_recall, cm_counts_one, many_recall, cm_counts_many
    )
    micro_precision = calc_micro_metric(
        one_precision, cm_counts_one, many_precision, cm_counts_many
    )
    micro_f1 = calc_micro_metric(one_f1, cm_counts_one, many_f1, cm_counts_many)

    if verbose:
        print("One recall", one_recall)
        print("One precision", one_precision)
        print("One f1", one_f1)
        print("One support", cm_counts_one)
        print("Many recall", many_recall)
        print("Many precision", many_precision)
        print("Many f1", many_f1)
        print("Many support", cm_counts_many)

    final_metrics = {
        "macro_recall": macro_recall,
        "macro_precision": macro_precision,
        "macro_f1": macro_f1,
        "micro_recall": micro_recall,
        "micro_precision": micro_precision,
        "micro_f1": micro_f1,
    }
    return final_metrics
