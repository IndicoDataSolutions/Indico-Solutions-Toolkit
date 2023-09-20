from dataclasses import dataclass

from .documents import Document
from .errors import MultiValueError, ResultError
from .reviews import Review


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
            raise MultiValueError(
                f"This submission contains {len(self.documents)} documents. "
                "Use `Submission.documents` instead."
            )

        return self.documents[0]

    @property
    def rejected(self) -> bool:
        return any(map(lambda review: review.rejected, self.reviews))

    @staticmethod
    def from_result(result: object) -> "Submission":
        """
        Factory function to produce a `Submission` from a result file dictionary.
        """
        if not isinstance(result, dict):
            raise TypeError(
                f"Expected `result` to be a `dict`. Got `{type(result)!r}`."
            )

        file_version = result.get("file_version", None)

        if file_version == 1:
            return Submission._from_result_v1(result)
        elif file_version == 2:
            return Submission._from_result_v2(result)
        elif file_version == 3:
            return Submission._from_result_v3(result)
        else:
            raise ResultError(f"Unknown file version `{file_version!r}`.")

    @staticmethod
    def _from_result_v1(result: dict[str, object]) -> "Submission":
        ...

    @staticmethod
    def _from_result_v2(result: dict[str, object]) -> "Submission":
        ...

    @staticmethod
    def _from_result_v3(result: dict[str, object]) -> "Submission":
        ...
