from typing import List, Dict
from collections import defaultdict
import fitz
from fitz import Page
from fitz.utils import getColor, getColorList
from faker import Faker
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
        if not path_to_pdf.lower().endswith(".pdf"):
            raise ToolkitInstantiationError(
                f"Highlighter requires PDF files, not {path_to_pdf[-4:]}"
            )
        self.path_to_pdf = path_to_pdf

    def set_mapped_positions(self, mapped_positions):
        """
        Call this method instead of the super class's collect_tokens method if the token positions are already mapped.
        Arguments:
            mapped_positions (List[dict])
        """
        self._mapped_positions = mapped_positions

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
                    annotation = self._get_annotation(token["position"], xnorm, ynorm)
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

    def redact_pdf(
        self,
        output_path: str,
        page_dimensions: List[dict],
        color_black: bool = True
    ) -> int:
        """
        Redact predicted text from a copy of a source PDF. Currently, you still need to convert
        your PDF to image files afterward to ensure PI is fully removed from the underlying data.

        Returns number of redactions

        Arguments:
            output_path {str} -- path of labeled PDF copy to create (set to same as pdf_path to overwrite)
            page_dimensions: {List[dict]} -- page heights and widths from ondocument OCR result, see
                                              Ondoc class and page_heights_and_widths property
            color_black {bool} -- if True, redactions are made with a black mark, else they are made with a white mark
        """
        num_redactions = 0
        if color_black:
            color = (0, 0, 0)
        else:
            color = (1, 1, 1)
        with fitz.open(self.path_to_pdf) as doc:
            for doc_page, tokens in self.mapped_positions_by_page.items():
                page = doc[doc_page]
                xnorm = page.rect[2] / page_dimensions[doc_page]["width"]
                ynorm = page.rect[3] / page_dimensions[doc_page]["height"]
                for token in tokens:
                    annotation = self._get_annotation(token["position"], xnorm, ynorm)
                    page.add_redact_annot(annotation, fill=color)
                num_redactions += sum([1 for _ in page.annots()])
                page.apply_redactions()
            doc.save(output_path)
        print(
            f"*Important* to ensure that underlying data can't be recovered, convert {output_path} to a png, tif, or scanned pdf file"
        )
        return num_redactions

    def redact_and_replace(
        self,
        output_path: str,
        page_dimensions: List[dict],
        fill_text: dict
    ) -> int:
        """
        Redact predicted text from a copy of a source PDF and replace if with fake values based on 
        label keys. For a full list of fake data options, see: https://github.com/joke2k/faker). 

        If no label found, defaults to redact with white color

        Returns number of redactions 

        Arguments:
            output_path {str} -- path of labeled PDF copy to create (set to same as pdf_path to overwrite)
            page_dimensions: {List[dict]} -- page heights and widths from ondocument OCR result, see
                                              Ondoc class and page_heights_and_widths property
            fill_text {dict} -- a dictionary where the keys are your labels and the val is an option from the
                                faker library. Possible options include 'text', 'company', 'currency', 'numerify',
                                'address', 'name', 'company_email', 'date' and many more. With 'numerify' and
                                'text', fake data will match the length of the redacted data.
        Example:
            # add a key to fill_text for each label in your extraction task w/ allowed fake data method
            fill_text = dict(member='name', birthday='date', invoice_number='numerify')
            highlight.redact_and_replace('source.pdf', 'redacted.pdf', fill_text=fill_text)
        """
        num_redactions = 0
        fake = Faker()
        with fitz.open(self.path_to_pdf) as doc:
            for pred in self._predictions:
                pred_positions = [pos for pos in sorted(self._mapped_positions, key=lambda x: x["position"]["bbLeft"]) if pos["text"] == pred["text"]]
                pred_position = pred_positions[0]
                # Adjust bbRight to contain right bounding box of pred instead of token
                pred_position["position"]["bbRight"] = pred_positions[-1]["position"]["bbRight"]
                doc_page = pred_position["page_num"]
                page = doc[doc_page]
                xnorm = page.rect[2] / page_dimensions[doc_page]["width"]
                ynorm = page.rect[3] / page_dimensions[doc_page]["height"]
                annotation = self._get_annotation(pred_position["position"], xnorm, ynorm)
                if "label" in pred and pred["label"] in fill_text:
                    label_type = fill_text[pred["label"]]
                    if label_type == "numerify":
                        text = getattr(fake, label_type)(len(pred["text"]) * "#")
                    elif label_type == "text":
                        text = getattr(fake, label_type)(max(5, len(pred["text"])))
                    else:
                        text = getattr(fake, label_type)()
                    page.add_redact_annot(
                        annotation, text=text, fill=False, fontsize=15
                    )
                else:
                    # second line of single prediction redacted
                    page.add_redact_annot(annotation, fill=(1, 1, 1))
                num_redactions += sum([1 for _ in page.annots()])
                page.apply_redactions()
            doc.save(output_path)
        print(
            f"*Important* to ensure that underlying data can't be recovered, convert {output_path} to a png, tif, or scanned pdf file"
        )
        return num_redactions

    def _get_annotation(
        self, 
        position: List, 
        xnorm: float, 
        ynorm: float
    ) -> fitz.Rect:
        annotation = fitz.Rect(
            position["bbLeft"] * xnorm,
            position["bbTop"] * ynorm,
            position["bbRight"] * xnorm,
            position["bbBot"] * ynorm,
        )
        # ensure that we cover a bit more than the bounding box
        inflater = annotation.height * 0.1
        annotation.x0, annotation.y0 = (
            annotation.x0 - inflater,
            annotation.y0 - inflater,
        )
        annotation.x1, annotation.y1 = (
            annotation.x1 + inflater,
            annotation.y1 + inflater,
        )
        return annotation
    
    def _get_new_metadata(self, metadata: dict, to_add: dict) -> dict:
        for key, val in to_add.items():
            metadata[key] = val
        return metadata

    def _get_page_label_counts(self, tokens: List[dict]) -> Dict[str, int]:
        already_found = []
        unique_preds = []
        for token in tokens:
            if token["prediction_index"] not in already_found:
                already_found.append(token["prediction_index"])
                unique_preds.append(token)
        return Extractions(unique_preds).label_count_dict

    def get_label_color_hash(self) -> dict:
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
