from dataclasses import dataclass

from .documents import Document
from .errors import MultipleValuesError, ResultFileError
from .reviews import Review
from .utils import exists, get


@dataclass
class Submission:
    id: int
    version: int
    documents: list[Document]
    reviews: list[Review]

    @property
    def bundled(self) -> bool:
        return len(self.documents) > 1

    @property
    def document(self) -> Document:
        if self.bundled:
            raise MultipleValuesError(
                f"Submission has {len(self.documents)} documents. "
                "Use `Submission.documents` instead."
            )

        return self.documents[0]

    @property
    def rejected(self) -> bool:
        return any(map(lambda review: review.rejected, self.reviews))

    @classmethod
    def from_result(cls, result: object) -> "Submission":
        """
        Factory function to produce a `Submission` from a result file dictionary.
        """
        version = get(result, "file_version", int)

        if version == 1:
            return cls._from_v1_result(result)
        elif version == 2:
            return cls._from_v2_result(result)
        elif version == 3:
            return cls._from_v3_result(result)
        else:
            raise ResultFileError(f"Unknown file version `{version!r}`.")

    @staticmethod
    def _from_v1_result(result: object) -> "Submission":
        """
        Classify, Extract, and Classify+Extract Workflows.
        """
        if exists(result, "results", dict) and not exists(result, "reviews_meta", list):
            raise ResultFileError(
                "Result has no review information. "
                "Use `SubmissionResult` to retrieve the result."
            )

        reviews_meta = get(result, "reviews_meta", list)

        # Unreviewed results retrieved through `SubmissionResult` have
        # { "reviews_meta": [{ "review_id": null }] }
        if reviews_meta and exists(reviews_meta[0], "review_id", int):
            reviews = list(map(Review._from_v1_result, reviews_meta))
        else:
            reviews = []

        return Submission(
            id=get(result, "submission_id", int),
            version=1,
            documents=[Document._from_v1_result(result, reviews)],
            reviews=reviews,
        )

    @staticmethod
    def _from_v2_result(result: object) -> "Submission":
        """
        Bundled Submission Workflows.
        """
        ...

    @staticmethod
    def _from_v3_result(result: object) -> "Submission":
        """
        Classify+Unbundle Workflows.
        """
        ...
