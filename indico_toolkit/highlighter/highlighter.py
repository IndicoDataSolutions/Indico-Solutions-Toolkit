from typing import List
from collections import defaultdict
import fitz
from fitz.utils import getColor
from indico_toolkit.association import ExtractedTokens
from indico_toolkit.pipelines import FileProcessing
from indico_toolkit.types import Extractions

# TODO: add redact and replace data class


class Highlighter(ExtractedTokens):
    def __init__(self, predictions: List[dict], path_to_pdf: str):
        super().__init__(predictions)
        self.path_to_pdf = path_to_pdf

    def highlight_pdf(
        self,
        output_path: str,
        page_dimensions: List[dict],
        include_toc: bool = False,
        color_map: dict = None,
    ):
        """
        Highlights predictions onto a copy of source PDF with the option to include a table of contents
        
        Arguments:
            output_path {str} -- path of labeled PDF copy to create (set to same as pdf_path to overwrite)
             page_dimensions: {List[dict]} -- page heights and widths from ondocument OCR result, see 
                                              Ondoc class and page_heights_and_widths property
            include_toc {bool} -- if True, insert a table of contents of what annotations were made and on what page
            # TODO: add color_map description
        """
        if not color_map:
            color_map = defaultdict(lambda: "yellow")
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
