from pathlib import Path
from typing import Literal

import pandas as pd
from rdetoolkit.rde2util import CharDecEncoding

from modules_xrd.interfaces import IInputFileParser


class FileReader(IInputFileParser):
    """Reads and processes structured ras files into data and metadata blocks.

    This class is responsible for reading structured files which have specific patterns for data and metadata.
    It then separates the contents into data blocks and metadata blocks.

    Attributes:
        data (dict[str, pd.DataFrame]): Dictionary to store separated data blocks.
        meta (dict[str, list[str]]): Dictionary to store separated metadata blocks.

    """

    def __init__(self, config: dict):
        self.data: dict[str, pd.DataFrame] = {}
        self.region_num = 0
        self.config = config

    @staticmethod
    def determine_delimiter(file_path: Path) -> Literal["\t", " "]:
        r"""Determine delimiter.

        MEMO: If there are the same number of tabs and spaces,
            they should be tab-separated. (That's absurd.)
        MEMO: Redundant writing.

        Args:
            file_path (Path): measurement file.

        Returns:
            tuple[str, str]: [(r'\t' or ' '), ('_tab' or '_space')]

        """
        tab_count = 0
        space_count = 0

        enc = CharDecEncoding.detect_text_file_encoding(file_path)
        if enc in ["macroman", "mac_roman"]:
            # False character code detection
            enc = "cp932"

        with open(file_path, encoding=enc) as file:
            for line in file:
                tab_count += line.count('\t')
                space_count += line.count(' ')

        if space_count > tab_count:
            return " "
        return "\t"

    def get_files_from_rasx(self, rasx_path: Path) -> list[str]:
        """Substance is in rigaku/rasx/inputfile_handler.py (only .rasx)."""
        return []
