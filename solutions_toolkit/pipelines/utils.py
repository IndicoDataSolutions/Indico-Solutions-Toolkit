import os
from typing import Tuple, List


def get_file_paths(
    path_to_dir: str, accepted_types: Tuple[str] = ("pdf", "tiff", "tif", "doc", "docx")
) -> List[str]:
    """
    Recursively find all file in specified types within a target directory
    Args:
        path_to_dir (str): root directory containing files
        accepted_types (Tuple[str], optional): Valid extensions types to process . Defaults to ("pdf", "tiff", "tif", "doc", "docx").

    Raises:
        Exception: Must have at least 1 valid file

    Returns:
        List[str]: list of full filepaths
    """
    file_paths = []
    for root, _, files in os.walk(path_to_dir):
        for name in files:
            if name.lower().endswith(accepted_types):
                file_paths.append(os.path.join(root, name))
    if len(file_paths) == 0:
        raise Exception(f"There are no files ending with {accepted_types} in {path_to_dir}")
    return file_paths
