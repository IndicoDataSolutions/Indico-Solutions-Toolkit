from dataclasses import dataclass
from typing import List

@dataclass
class Example:
    id: int
    data_file_name: str

class ExampleList:
    def __init__(self, examples: List[Example]):
        self.examples = examples
    
    def get_example(self, example_id: int) -> Example:
        """
        Returns example with matching example_id. If no matching example id found, return None
        """
        for example in self.examples:
            if example.id == example_id:
                return example
        return None
    
    def get_example_id(self, example_data_file_name: str) -> int:
        """
        Returns id for a specific example with the same name as example_data_file_name. If no matching example found, return None
        Assumes no duplicate filenames in dataset
        """
        for example in self.examples:
            if example.data_file_name == example_data_file_name:
                return example.id
        return None

@dataclass
class TokenSpanInput:
    start: int
    end: int
    pageNum: int

@dataclass
class SpatialSpanInput:
    top: int
    bottom: int
    left: int
    right: int
    pageNum: int

@dataclass
class LabelInst:
    clsId: int
    spans: List[TokenSpanInput] = None
    bounds: List[SpatialSpanInput] = None

@dataclass
class LabelInput:
    exampleId: int
    targets: List[LabelInst]
    rejected: bool = None
    override: bool = None
    partial: bool = None