"""
Dump classifications and extractions from result files to a CSV file.
"""

import csv
from collections.abc import Iterable, Iterator
from pathlib import Path

import arguably

from indico_toolkit import results


def final_predictions(result: results.Result) -> Iterator[dict[str, object]]:
    for prediction in result.final:
        if isinstance(prediction, results.Classification):
            yield {
                "submission_id": result.submission_id,
                "document_id": prediction.document.id,
                "model": prediction.model.name,
                "field": "Classification",
                "value": prediction.label,
                "confidence": prediction.confidence,
            }
        elif isinstance(prediction, results.Extraction):
            yield {
                "submission_id": result.submission_id,
                "document_id": prediction.document.id,
                "model": prediction.model.name,
                "field": prediction.label,
                "value": prediction.text,
                "confidence": prediction.confidence,
            }


def predictions_from_files(result_files: Iterable[Path]) -> Iterator[dict[str, object]]:
    for result_file in result_files:
        result = results.load(result_file)
        yield from final_predictions(result)


@arguably.command
def convert_to_csv(
    *result_files: Path,
    csv_file: Path = Path("predictions.csv"),
) -> None:
    """
    Dump classifications and extractions from result files to a CSV file.
    """
    with csv_file.open("w", newline="") as file:
        csv.DictWriter(
            file,
            fieldnames=[
                "submission_id",
                "document_id",
                "model",
                "field",
                "value",
                "confidence",
            ],
        ).writerows(
            predictions_from_files(result_files),
        )


if __name__ == "__main__":
    arguably.run()
