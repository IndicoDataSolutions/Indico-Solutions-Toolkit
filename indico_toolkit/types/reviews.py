from dataclasses import dataclass
from enum import StrEnum

from .errors import ResultFileError
from .utils import get


class ReviewType(StrEnum):
    ADMIN = "admin"
    AUTO = "auto"
    MANUAL = "manual"


@dataclass
class Review:
    id: int
    reviewer_id: int
    notes: str
    rejected: bool
    type: ReviewType

    @staticmethod
    def _from_v1_result(review: object) -> "Review":
        """
        Classify, Extract, and Classify+Extract Workflows.
        """
        try:
            notes = get(review, "review_notes", str)
        except ResultFileError:
            notes = ""  # Notes may be null.

        return Review(
            id=get(review, "review_id", int),
            reviewer_id=get(review, "reviewer_id", int),
            notes=notes,
            rejected=get(review, "review_rejected", bool),
            type=ReviewType(get(review, "review_type", str)),
        )
