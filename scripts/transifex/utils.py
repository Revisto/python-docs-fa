# filepath: scripts/transifex_utils/utils.py
import re
from pathlib import Path
from .config import RESOURCE_NAME_MAP


def slug_to_file_path(slug: str) -> Path:
    """
    Converts a Transifex resource slug to a local .po file path.
    Handles legacy mappings and specific formatting rules.
    """
    file_path_str = RESOURCE_NAME_MAP.get(slug, slug)
    file_path_str = file_path_str.replace("--", "/")
    if re.fullmatch(r"\d+_\d+", file_path_str):
        file_path_str = file_path_str.replace("_", ".", 1)
    file_path_str += ".po"
    return Path(file_path_str)
