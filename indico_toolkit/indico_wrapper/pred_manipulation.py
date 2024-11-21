from typing import List


class ManipulatePreds:
    """
    Class to help expand prediction text and indexing via OCR data.
    """

    def __init__(self, ocr_tokens: List[dict], preds: List[dict]):
        self.ocr_tokens = ocr_tokens
        self.predictions = preds

    def expand_predictions(self, pred_start: int, pred_end: int) -> dict:
        """
        Expand predictions and boundaries to match that of OCR data.

        Args:
            pred_start (int): Starting prediction index
            pred_end (int): Ending prediction index
        Returns:
            dict: Returns expanded prediction dictionary
        """
        expanded_start, expanded_end = pred_start, pred_end
        pred_index = None

        # Find index value of bounded prediction
        for index, pred in enumerate(self.predictions):
            if pred["start"] == pred_start or pred["end"] == pred_end:
                pred_index = index
                break

        if pred_index is None:
            raise ValueError("No matching prediction found.")

        # Validate current prediction needs expanding
        original_text = self.predictions[pred_index]["text"]
        ocr_text_initial = self._get_ocr_text(pred_start, pred_end)
        if original_text == ocr_text_initial:
            print("No expansion needed")
            return self.predictions[pred_index]

        # Use overlapping boundaries and expand text / boundaries to match OCR data
        for token in self.ocr_tokens:
            if token["doc_offset"]["start"] <= pred_start <= token["doc_offset"]["end"]:
                expanded_start = min(expanded_start, token["doc_offset"]["start"])
            if token["doc_offset"]["start"] <= pred_end <= token["doc_offset"]["end"]:
                expanded_end = max(expanded_end, token["doc_offset"]["end"])

        expanded_text = self._get_ocr_text(expanded_start, expanded_end)
        if expanded_text != ocr_text_initial:
            raise ValueError("Expanded text does not match the OCR text.")

        if expanded_text == ocr_text_initial:
            # Update prediction
            self.predictions[pred_index]["start"] = expanded_start
            self.predictions[pred_index]["end"] = expanded_end
            self.predictions[pred_index]["text"] = expanded_text

        return self.predictions[pred_index]

    def is_token_nearby(
        self, ocr_start: int, ocr_end: int, search_tokens: List[str], distance: int
    ) -> bool:
        """
        A function that returns a boolean if specified token(s) are found within a given distance.

        Args:
            ocr_start (int): Starting OCR index
            ocr_end (int): Ending OCR index
            search_tokens (List[str]): A list of strings to be searched for, case senstive.
            distance (int): The amount of tokens examined, forward and backwards, in the search.
        Returns:
            bool: Returns True if a search token is found.
        """
        token_index = None
        for index, token in enumerate(self.ocr_tokens):
            if (
                token["doc_offset"]["start"] == ocr_start
                and token["doc_offset"]["end"] == ocr_end
            ):
                token_index = index
                break

        if token_index:
            for i in range(max(0, token_index - distance), token_index):
                if self.ocr_tokens[i]["text"] in search_tokens:
                    return True

            for i in range(
                token_index + 1, min(len(self.ocr_tokens), token_index + distance + 1)
            ):
                if self.ocr_tokens[i]["text"] in search_tokens:
                    return True

        else:
            raise ValueError("No token found with specified bounds.")

        return False

    def _get_ocr_text(self, start: int, end: int) -> str:
        """
        Args:
            start (int): Starting OCR token index
            end (int): Ending OCR token index
        Returns:
            str: Full token text found within the specified boundaries.
        """
        text = ""
        for token in self.ocr_tokens:
            if token["doc_offset"]["end"] <= start:
                continue
            if token["doc_offset"]["start"] >= end:
                break
            text += token["text"] + " "
        return text.strip()
