from typing import List, Union
from collections import defaultdict
import fitz
from fitz import Page
from fitz.utils import getColor, getColorList
import numpy as np

from indico_toolkit.association import ExtractedTokens
from indico_toolkit.pipelines import FileProcessing
from indico_toolkit.types import Extractions
from indico_toolkit import ToolkitInstantiationError

# TODO: add redact and replace data class


class Highlighter(ExtractedTokens):
    def __init__(self, predictions: List[dict], path_to_pdf: str, mapped_positions: List[dict] = []):
        """
        Highlight predictions using source PDF documents
        Args:
            predictions (List[dict]): Extraction predictions
            path_to_pdf (str): Path to the predictions' doc
        Kwargs:
            mapped_positions (List[dict]): if you have already collected the positions of the tokens to highlight,
                                           pass them in here and skip the "collect_tokens" call. You can also 
                                           pass a filler value for "predictions"
        Example:
            highlight = Highlighter(preds, "./myfile.pdf")
            highlight.collect_tokens(ondoc.token_objects)
            highlight.highlight_pdf(
                    "./highlighted_myfile.pdf",
                    ondoc.page_heights_and_widths,
                    all_yellow_highlight=False
                )
        """
        super().__init__(predictions)
        self._mapped_positions = mapped_positions
        if not path_to_pdf.lower().endswith(".pdf"):
            raise ToolkitInstantiationError(
                f"Highlighter requires PDF files, not {path_to_pdf[-4:]}"
            )
        self.path_to_pdf = path_to_pdf

    def highlight_pdf(
        self,
        output_path: str,
        page_dimensions: List[dict],
        all_yellow_highlight: bool = True,
        color_map: dict = None,
        add_label_annotations: bool = False,
        add_bookmarks: bool = True,
        highlight_opacity: float = 0.4,
        metadata: dict = None,
    ):
        """
        Highlights extraction predictions onto a copy of source PDF

        Arguments:
            output_path {str} -- path of labeled PDF copy to create (set to same as pdf_path to overwrite)
             page_dimensions: {List[dict]} -- page heights and widths from ondocument OCR result, see
                                              Ondoc class and page_heights_and_widths property
            all_yellow_highlight (bool) -- if True, all highlights are yellow, otherwise, each field gets a unique color
            color_map (dict) -- Optionally, specify what highlight color to apply to each field, use get_color_list() method
                                to see available colors. Can alternatively put an RGB (normalized 0-1) tuple
            add_bookmarks (book) -- if True, adds per page bookmarks of what labels are found on that page
            add_label_annotations (bool) -- if True, annotates the label name in small red text above the highlights
            highlight_opacity: (float) -- 0 to 1 opacity of highlight.
            metadata: (dict) -- Add metadata to a pdf's properties

        """
        if all_yellow_highlight:
            color_map = defaultdict(lambda: "yellow")
        elif color_map is None:
            color_map = self.get_label_color_hash()
        with fitz.open(self.path_to_pdf) as doc:
            bookmarks = []
            for doc_page, tokens in self.mapped_positions_by_page.items():
                labels_on_page = set()
                page = doc[doc_page]
                xnorm = page.rect[2] / page_dimensions[doc_page]["width"]
                ynorm = page.rect[3] / page_dimensions[doc_page]["height"]
                for token in tokens:
                    annotation = fitz.Rect(
                        token["position"]["bbLeft"] * xnorm,
                        token["position"]["bbTop"] * ynorm,
                        token["position"]["bbRight"] * xnorm,
                        token["position"]["bbBot"] * ynorm,
                    )
                    labels_on_page.add(token["label"])
                    color = color_map[token["label"]]
                    if isinstance(color, str):
                        color = getColor(color)
                    ann = page.add_highlight_annot(annotation)
                    ann.set_opacity(highlight_opacity)
                    ann.set_colors(stroke=color)
                    ann.update()
                bookmarks.extend(
                    [[1, i.replace(" ", "_"), doc_page + 1] for i in labels_on_page]
                )
                if add_label_annotations:
                    self._add_label_annotations(page, tokens, xnorm, ynorm)
            if add_bookmarks:
                doc.set_toc(bookmarks)
            if metadata:
                new_meta = self._get_new_metadata(doc.metadata, metadata)
                doc.set_metadata(new_meta)
            doc.save(output_path)

    def _get_new_metadata(self, metadata: dict, to_add: dict) -> dict:
        for key, val in to_add.items():
            metadata[key] = val
        return metadata

    def _get_page_label_counts(self, tokens: List[dict]):
        already_found = []
        unique_preds = []
        for token in tokens:
            if token["prediction_index"] not in already_found:
                already_found.append(token["prediction_index"])
                unique_preds.append(token)
        return Extractions(unique_preds).label_count_dict

    def get_label_color_hash(self):
        """
        Create a unique random highlight color for each label in hash table
        """
        label_set = Extractions.get_label_set(self._predictions)
        colors = np.random.choice(
            self.get_color_list(), size=len(label_set), replace=False
        )
        colors = [getColor(i) for i in colors]
        return dict(zip(label_set, colors))

    def get_color_list(self) -> List[str]:
        """
        Get list of available highlight colors
        """
        return [
            i
            for i in getColorList()
            if "dark" not in i.lower()
            and "white" not in i.lower()
            and "black" not in i.lower()
        ]

    def _add_label_annotations(
        self,
        page: Page,
        tokens: List[dict],
        xnorm: float,
        ynorm: float,
        font_size: int = 5,
        color: str = "red",
    ):
        """
        Annotate the label name above highlights on the source document

        Args:
            page (Page): the fitz page object
            tokens (List[dict]): the tokens for current page
            xnorm (float): the xnorm value for the page
            ynorm (float): the ynorm value for the page
            font_size (int, optional): label font size. Defaults to 5.
            color (str, optional): label color. Defaults to "red".
        """
        captured_preds = set()
        for token in tokens:
            if token["prediction_index"] not in captured_preds:
                text_height = int(
                    (token["position"]["bottom"] - token["position"]["top"]) * 0.05
                )
                point = fitz.Point(
                    token["position"]["left"] * xnorm,
                    token["position"]["top"] * ynorm - text_height,
                )
                page.insert_text(point, token["label"], font_size, color=getColor(color))
                captured_preds.add(token["prediction_index"])
