from dataclasses import dataclass

from .documents import Document
from .errors import MultiValueError
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
        id = result.get("submission_id")
        version = result.get("file_version")
        if version == 1:
            document = Document.from_result(result)
            documents = [document]
        else:
            documents = []
            for submission_result in result["submission_results"]:
                submission_result["file_version"] = result["file_version"]
                submission_result["submission_id"] = result["submission_id"]
                submission_result["modelgroup_metadata"] = result["modelgroup_metadata"]
                documents.append(Document.from_result(submission_result))
            document = documents[0]

        return Submission(
            id=id, version=version, document=document, documents=documents
        )
