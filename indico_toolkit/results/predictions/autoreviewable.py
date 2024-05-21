from dataclasses import dataclass

from .predictions import Prediction


@dataclass
class AutoReviewable(Prediction):
    accepted: bool
    rejected: bool

    def accept(self) -> None:
        self.accepted = True
        self.rejected = False

    def unaccept(self) -> None:
        self.accepted = False

    def reject(self) -> None:
        self.accepted = False
        self.rejected = True

    def unreject(self) -> None:
        self.rejected = False
