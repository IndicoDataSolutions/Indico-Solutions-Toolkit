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
    def __init__(self, predictions: List[dict], path_to_pdf: str):
        """
        Highlight predictions using source PDF documents
        Args:
            predictions (List[dict]): Extraction predictions
            path_to_pdf (str): Path to the predictions' doc

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
        include_toc: bool = False,
        color_map: dict = None,
        add_label_annotations: bool = False,
    ):
        """
        Highlights extraction predictions onto a copy of source PDF
        
        Arguments:
            output_path {str} -- path of labeled PDF copy to create (set to same as pdf_path to overwrite)
             page_dimensions: {List[dict]} -- page heights and widths from ondocument OCR result, see 
                                              Ondoc class and page_heights_and_widths property
            all_yellow_highlight (bool) -- if True, all highlights are yellow, otherwise, each field gets a unique color
            include_toc {bool} -- if True, insert a table of contents of what annotations were made and on what page
            color_map (dict) -- Optionally, specify what highlight color to apply to each field, use get_color_list() method
                                to see available colors.
            add_label_annotations (bool) -- if True, annotates the label name in small red text above the highlights
                                
        """
        if all_yellow_highlight:
            color_map = defaultdict(lambda: "yellow")
        elif color_map is None:
            color_map = self.get_label_color_hash()
        with fitz.open(self.path_to_pdf) as doc:
            for doc_page, tokens in self.mapped_positions_by_page.items():
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
                    color = color_map[token["label"]]
                    ann = page.addHighlightAnnot(annotation)
                    ann.setOpacity(0.5)
                    ann.setColors(stroke=getColor(color))
                    ann.update()
                if add_label_annotations:
                    self._add_label_annotations(page, tokens, xnorm, ynorm)
            if include_toc:
                toc_text = self._get_toc_text()
                doc.insertPage(0, text=toc_text, fontsize=13)
            doc.save(output_path)

    def _get_toc_text(self) -> str:
        """
        If a table of contents is requested, formats and returns the page text
        """
        filename = FileProcessing.file_name_from_path(self.path_to_pdf)
        base_text = f"File: {filename}\n\nPages w/ Extractions found:\n\n"
        page_strings = list()
        for page, tokens in self.mapped_positions_by_page.items():
            label_counts = self._get_page_label_counts(tokens)
            content = ", ".join(f"{key} ({val})" for key, val in label_counts.items())
            page_strings.append(f"Page {page + 1}: {content}")
        return base_text + "\n".join(page_strings)

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
        label_set = Extractions.get_extraction_labels_set(self._predictions)
        colors = np.random.choice(
            self.get_color_list(), size=len(label_set), replace=False
        )
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
                page.insertText(point, token["label"], font_size, color=getColor(color))
                captured_preds.add(token["prediction_index"])
