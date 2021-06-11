import os
from os.path import isfile
from pathlib import Path
from typing import List, Tuple, Callable, Iterable


class FileProcessing:
    """
    Class to support common file processing operations
    """
    def __init__(self, file_paths: List[str] = None):
        if file_paths is None:
            file_paths = []
        self.file_paths: List[str] = file_paths
        self.invalid_suffix_paths = set()

    def get_file_paths_from_dir(
        self,
        path_to_dir: str,
        accepted_types: Tuple[str] = ("pdf", "tiff", "tif", "doc", "docx"),
        recursive_search: bool = False,
    ):
        """
        Recursively find all file in specified types within a target directory
        Args:
            path_to_dir (str): root directory containing files
            accepted_types (Tuple[str], optional): Valid extensions types to process . Defaults to ("pdf", "tiff", "tif", "doc", "docx").
            recursive_search (bool): search sub directories as well. Defaults to False.

        Raises:
            Exception: Must have at least 1 valid file
        """
        if recursive_search:
            self._recursive_file_search(path_to_dir, accepted_types)
        else:
            self._non_recursive_file_search(path_to_dir, accepted_types)

        if len(self.file_paths) == 0:
            raise Exception(
                f"There are no files ending with {accepted_types} in {path_to_dir}"
            )

        print(
            f"Found {len(self.file_paths)} valid files and {len(self.invalid_suffix_paths)} paths with invalid suffixes."
        )


    def batch_files(self, batch_size: int = 20) -> List[str]:
        for i in range(0, len(self.file_paths), batch_size):
            yield self.file_paths[i : i + batch_size]

    def remove_files_if_processed(self, processed_files: Iterable[str]):
        """
        Removes files from self.file_paths if they are part of provided file iterable
        Args:
            processed_files (Iterable[str]): iterable of file names, NOT full paths, e.g. ["invoice.pdf",]
        """
        unprocessed_filepaths = []
        for filepath in self.file_paths:
            if self.file_name_from_path(filepath) not in processed_files:
                unprocessed_filepaths.append(filepath)
        print(f"Removing {len(self.file_paths) - len(unprocessed_filepaths)} files from file_paths")
        self.file_paths = unprocessed_filepaths

    @staticmethod
    def file_exists(path_to_file: str) -> bool:
        return os.path.isfile(path_to_file)

    @property
    def parent_directory_of_filepaths(self) -> List[str]:
        return [Path(i).parent.name for i in self.file_paths]

    @staticmethod
    def join_paths(start_path:str, end_path: str) -> str:
        return os.path.join(start_path, end_path)

    @staticmethod
    def get_file_name_without_suffix(filepath: str) -> str:
        return Path(filepath).stem

    @staticmethod
    def get_file_path_suffix(filepath: str) -> str:
        return Path(filepath).suffix

    @staticmethod
    def file_name_from_path(filepath: str) -> str:
        return Path(filepath).name
    
    @staticmethod
    def get_parent_path(filepath: str) -> str:
        return str(Path(filepath).parent)

    def __iter__(self):
        """
        Object is iterable on file_paths
        """
        current = 0
        while current < len(self.file_paths):
            yield self.file_paths[current]
            current += 1

    def _recursive_file_search(self, path_to_dir: str, accepted_types: Tuple[str]):
        for root, _, files in os.walk(path_to_dir):
            for name in files:
                if self._check_acceptable_suffix(name, accepted_types):
                    self.file_paths.append(os.path.join(root, name))
                else:
                    self.invalid_suffix_paths.add(os.path.join(root, name))

    def _non_recursive_file_search(self, path_to_dir: str, accepted_types: Tuple[str]):
        files = [os.path.join(path_to_dir, f) for f in os.listdir(path_to_dir)]
        for fpath in files:
            if self._check_acceptable_suffix(fpath, accepted_types):
                self.file_paths.append(fpath)
            elif isfile(fpath):
                self.invalid_suffix_paths.add(fpath)

    @staticmethod
    def _check_acceptable_suffix(string: str, accepted_suffixes: Tuple[str]) -> bool:
        if string.lower().endswith(accepted_suffixes):
            return True
        return False
