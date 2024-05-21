from dataclasses import dataclass
from typing import TYPE_CHECKING

from ..utils import get

if TYPE_CHECKING:
    from typing import Any


@dataclass(frozen=True, order=True)
class Group:
    id: int
    name: str
    index: int

    @staticmethod
    def from_dict(group: object) -> "Group":
        return Group(
            id=int(get(group, str, "group_id").split(":")[0]),
            name=get(group, str, "group_name"),
            index=get(group, int, "group_index"),
        )

    def to_dict(self) -> "dict[str, Any]":
        return {
            "group_id": f"{self.id}:{self.name}",
            "group_name": self.name,
            "group_index": self.index,
        }
