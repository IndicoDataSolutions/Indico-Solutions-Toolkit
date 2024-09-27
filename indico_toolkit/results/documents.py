from dataclasses import dataclass

from .utils import get


@dataclass(frozen=True, order=True)
class Document:
    id: int
    name: str
    etl_output_url: str
    full_text_url: str

    # Auto review changes must reproduce all model sections that were present in the
    # original result file. This may not be possible from the predictions alone--if a
    # model had an empty section because it didn't produce predictions or if all of
    # the predictions were removed to reject them. As such, the models seen when
    # parsing result files are tracked per-document so that the empty sections can be
    # reproduced later.
    _model_sections: "frozenset[str]"

    @staticmethod
    def from_v1_dict(result: object) -> "Document":
        """
        Create a `Document` from a v1 result file dictionary.
        """
        document_results = get(result, dict, "results", "document", "results")
        model_names = frozenset(document_results.keys())
        etl_output_url = get(result, str, "etl_output")
        full_text_url = etl_output_url.replace("etl_output.json", "full_text.txt")

        return Document(
            # v1 result files don't include document IDs or filenames.
            id=None,  # type: ignore[arg-type]
            name=None,  # type: ignore[arg-type]
            etl_output_url=etl_output_url,
            full_text_url=full_text_url,
            _model_sections=model_names,
        )

    @staticmethod
    def from_v3_dict(document: object) -> "Document":
        """
        Create a `Document` from a v3 document dictionary.
        """
        model_results = get(document, dict, "model_results", "ORIGINAL")
        model_ids = frozenset(model_results.keys())
        etl_output_url = get(document, str, "etl_output")
        full_text_url = etl_output_url.replace("etl_output.json", "full_text.txt")

        return Document(
            id=get(document, int, "submissionfile_id"),
            name=get(document, str, "input_filename"),
            etl_output_url=etl_output_url,
            full_text_url=full_text_url,
            _model_sections=model_ids,
        )
