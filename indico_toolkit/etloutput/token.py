from dataclasses import dataclass

from .utilities import get


@dataclass(frozen=True)
class Token:
    text: str
    # Span
    start: int
    end: int
    # Bounding box
    page: int
    top: int
    left: int
    right: int
    bottom: int

    def __lt__(self, other: "Token") -> bool:
        """
        By default, tokens are sorted in bounding box order with vertical hysteresis.
        Those on the same line are sorted left-to-right, even when later tokens are
        slightly higher than earlier ones.

        Tokens can also be sorted in span order: `tokens.sort(key=attrgetter("start"))`.
        """
        return (
            self.page < other.page
            or (self.page == other.page and self.bottom < other.top)
            or (
                self.page == other.page
                and self.top < other.bottom
                and self.left < other.left
            )
        )

    @staticmethod
    def from_dict(token: object) -> "Token":
        """
        Create a `Token` from a v1 or v3 token dictionary.
        """
        return Token(
            text=get(token, str, "text"),
            start=get(token, int, "doc_offset", "start"),
            end=get(token, int, "doc_offset", "end"),
            page=get(token, int, "page_num"),
            top=get(token, int, "position", "top"),
            left=get(token, int, "position", "left"),
            right=get(token, int, "position", "right"),
            bottom=get(token, int, "position", "bottom"),
        )
