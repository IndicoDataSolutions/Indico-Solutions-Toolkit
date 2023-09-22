from dataclasses import dataclass
from enum import StrEnum


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
    def from_result(result: dict[str, object]) -> "Review":
        """
        Factory function to produce a `Review` from a portion of a result file.
        """
        ...
