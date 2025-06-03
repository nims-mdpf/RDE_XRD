from __future__ import annotations

import os
import zipfile
from pathlib import Path
from typing import Final

import pandas as pd
from rdetoolkit.exceptions import StructuredError
from rdetoolkit.models.rde2types import RdeOutputResourcePath
from rdetoolkit.rde2util import CharDecEncoding

from modules_xrd.interfaces import IStructuredDataProcessor


class StructuredDataProcessor(IStructuredDataProcessor):
    """Template class for parsing structured data.

    This class serves as a template for the development team to read and parse structured data.
    It implements the IStructuredDataProcessor interface. Developers can use this template class
    as a foundation for adding specific file reading and parsing logic based on the project's
    requirements.

    Attributes:
        df_series_1 (pd.DataFrame): The first series of data.
        df_series_2 (pd.DataFrame): The second series of data.

    Example:
        csv_handler = StructuredDataProcessor()
        df = pd.DataFrame([[1,2,3],[4,5,6]])
        loaded_data = csv_handler.to_csv(df, 'file2.txt')

    """

    def __init__(self) -> None:
        self.df_series_1 = pd.DataFrame()
        self.df_series_2 = pd.DataFrame()

    def save_csv(
            self,
            resource_paths: RdeOutputResourcePath,
            dataframe: pd.DataFrame,
            region_num: int,
    ) -> None:
        """Save csv.

        Args:
            resource_paths (RdeOutputResourcePath): Paths to output resources for saving results.
            dataframe (pd.DataFrame): The data to save.
            region_num (int): Region numbers.

        """
        rename_save_path = self.reindex_savefilename(
            resource_paths.struct.joinpath(f"{resource_paths.rawfiles[0].stem}.csv"),
            region_num=region_num,
        )
        dataframe.to_csv(rename_save_path, index=False)

    def save_structured_contents(
        self,
        resource_paths: RdeOutputResourcePath,
        compressed_files: list[str],
    ) -> None:
        """Save a file with human-readable metadata to the specified folder.

        Args:
            resource_paths (RdeOutputResourcePath): Paths to output resources for saving results.
            compressed_files (list[str]): compressed files. (not use)

        Note:
            In RDE, the structured folder includes all files that are not included in main_image or other_image and should be outputted.

        """
        for cmpfile in compressed_files:
            basename = self._get_basename(cmpfile)
            contents = self._read_compressed_contents(str(cmpfile), str(resource_paths.rawfiles[0])) \
                if resource_paths.rawfiles[0] is not None \
                else self._read_text_contents(cmpfile)
            self._write_contents(resource_paths.struct.joinpath(basename), contents)

    def reindex_savefilename(self, filepath: str | Path, region_num: int) -> Path:
        """Indexing file names.

        Args:
            filepath (str | Path): File name before renaming.
            region_num (int): Region numbers.

        Returns:
            Path: Renamed file name.

        """
        single_region_num: Final[int] = 1
        multi_region_num: Final[int] = 2

        if isinstance(filepath, str):
            filepath = Path(filepath)

        if region_num > multi_region_num or region_num < single_region_num:
            err_msg = f"illegal region number: {region_num}"
            raise StructuredError(err_msg)
        if region_num == single_region_num:
            return filepath

        dirname = filepath.parent
        basename = filepath.stem
        suffix = filepath.suffix

        idx = 1
        while True:
            new_filename = f"{basename}_{idx}{suffix}"
            new_filepath = dirname / new_filename
            if not new_filepath.exists():
                break
            idx += 1

        return new_filepath

    def _get_basename(self, src_path: str | Path) -> str:
        """Get the basename of the source path."""
        if isinstance(src_path, Path):
            return src_path.name
        return os.path.basename(src_path)

    def _read_compressed_contents(self, src_path: str, compressed_filepath: str) -> str:
        """Read the contents of a compressed file."""
        with zipfile.ZipFile(compressed_filepath, "r") as rasx, rasx.open(src_path) as frasx:
            contents_bytes = frasx.read()
        _, ext = os.path.splitext(src_path)
        contents = contents_bytes.decode("utf-8") if ext not in [".rasx", ".zip"] else ""
        if not contents and isinstance(contents_bytes, bytes):
            contents = str(contents_bytes)
        return contents

    def _read_text_contents(self, src_path: str | Path) -> str:
        """Read the contents of a text file."""
        enc = CharDecEncoding.detect_text_file_encoding(src_path)
        with open(src_path, encoding=enc) as f:
            return f.read()

    def _write_contents(self, save_path: Path, contents: str) -> None:
        """Write the contents to the save path."""
        with open(save_path, mode="w", encoding="utf-8") as f:
            f.write(contents)
