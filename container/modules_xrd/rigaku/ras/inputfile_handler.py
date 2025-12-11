from __future__ import annotations

import re
from collections.abc import Generator
from pathlib import Path

import pandas as pd
from rdetoolkit.exceptions import StructuredError
from rdetoolkit.rde2util import CharDecEncoding

from modules_xrd.inputfile_handler import FileReader as XrdFileReader
from modules_xrd.interfaces import ExtendMetaType


class FileReader(XrdFileReader):
    """Reads and processes structured ras files into data and metadata blocks.

    This class is responsible for reading structured files which have specific patterns for data and metadata.
    It then separates the contents into data blocks and metadata blocks.

    Attributes:
        data (dict[str, pd.DataFrame]): Dictionary to store separated data blocks.
        meta (dict[str, list[str]]): Dictionary to store separated metadata blocks.

    """

    __mode__ = "ras"

    def __init__(self, config: dict):
        super().__init__(config)
        self.meta: dict[str, ExtendMetaType] = {}

    def read(self, srcpath: Path) -> Generator[tuple[pd.DataFrame, ExtendMetaType], None, None]:
        """Read the structured file and returns separated data and metadata.

        Args:
            srcpath (Path): The path of the structured file to read.

        Returns:
            tuple[tuple[pd.DataFrame, ExtendMetaType], ...]: A tuple containing two dictionaries -
            the first one for data blocks and the second one for metadata blocks.

        Raises:
            StructuredError: If the file is formatted incorrectly.

        """
        enc = CharDecEncoding.detect_text_file_encoding(srcpath)
        with open(srcpath, encoding=enc) as f:
            self.data, self.meta = self.split_data_meta(f.read())
        if not self.data or not self.meta:
            err_msg = f"Cannot read the file because it is formatted incorrectly: {srcpath}"
            raise StructuredError(err_msg)

        self.region_num = len(self.data.keys())
        for data_key, meta_key in zip(self.data, self.meta, strict=False):
            yield self.convert_dtype(self.data[data_key]), self.meta[meta_key]

    def get_region_number(self, *, input_path: Path | None = None) -> int:
        """Get the number of regions.

        Args:
            input_path (Path | None): Measurement file path.

        Returns:
            int: Number of regions.

        """
        if input_path is None:
            return self.region_num
        data_meta_mappings = [df_data for df_data, _ in self.read(input_path)]
        self.region_num = len(data_meta_mappings)
        return self.region_num

    def split_data_meta(self, contents: str) -> tuple[dict[str, pd.DataFrame], dict[str, ExtendMetaType]]:
        """Private method to split the contents into data and metadata blocks.

        Args:
            contents (str): The contents of the structured file as a string.

        Returns:
            tuple[dict[str, pd.DataFrame], dict[str, ExtendMetaType]]: A tuple containing two dictionaries -
            the first one for data blocks and the second one for metadata blocks.

        """
        meta_blocks: dict[str, ExtendMetaType] = {}
        data_blocks: dict[str, pd.DataFrame] = {}

        data_pattern = re.findall(r"\*RAS_INT_START\n(.*?)\*RAS_INT_END", contents, re.DOTALL)
        header_pattern = re.findall(r"\*RAS_HEADER_START\n(.*?)\*RAS_HEADER_END", contents, re.DOTALL)
        for i, (data_section, header_section) in enumerate(zip(data_pattern, header_pattern, strict=False), start=1):
            meta_blocks[f"series_meta{i}"] = header_section.strip().split("\n")
            header = self.make_header(meta_blocks[f"series_meta{i}"])

            # convert measured values to dataframes
            data_list = [line.split() for line in data_section.strip().split("\n")]
            df = pd.DataFrame(data_list)
            df[1] = (df[1].astype(float) * df[2].astype(float)).apply(lambda x: f"{x:.4f}")
            df = df.drop(2, axis=1)
            data_blocks[f"series_value{i}"] = df.set_axis(header, axis="columns")

        return data_blocks, meta_blocks

    def make_header(self, header_info: ExtendMetaType) -> list[str]:
        """Make a header using provided header information.

        Args:
            header_info (ExtendMetaType): The header information dictionary.

        Returns:
            list[str]: The constructed header string.

        """
        x_label = self.config['xrd']['meas_scan_axis_x']
        if not x_label:
            _x_label = self.search_element_with_substring(header_info, "MEAS_SCAN_AXIS_X")
            x_label = self.__validation_greek_characters(_x_label)
        x_unit = self.config['xrd']['meas_scan_unit_x']
        if not x_unit:
            x_unit = self.search_element_with_substring(header_info, "MEAS_SCAN_UNIT_X")
        y_label = self.config['xrd']['meas_scan_axis_y']
        if not y_label:
            y_label = "Intensity"
        y_unit = self.config['xrd']['meas_scan_unit_y']
        if not y_unit:
            y_unit = self.search_element_with_substring(header_info, "MEAS_SCAN_UNIT_Y")
        return [f"{x_label} ({x_unit})", f"{y_label} ({y_unit})"]

    def search_element_with_substring(self, header_info: ExtendMetaType, substring: str, *, pattern: str = r'"(.*?)"') -> str:
        """Search element with substring.

        Args:
            header_info (ExtendMetaType): The header information dictionary.
            substring (str): Element.
            pattern (str): Delimiter.

        Returns:
            str: Value of the relevant element.

        """
        substring_lists = [element for element in header_info if substring in element]
        _substring: str = ""
        if len(substring_lists) > 0:
            _substring = str(substring_lists[0])
        else:
            return ""

        match = re.search(pattern, _substring)
        return "" if match is None else match.group(1)

    def convert_dtype(self, dataframe: pd.DataFrame, *, totype: str = "float") -> pd.DataFrame:
        """Convert data type.

        Args:
            dataframe (pd.DataFrame): Data frame before conversion.
            totype (str): Converted data type.

        Returns:
            pd.DataFrame: Data frame after conversion.

        """
        return dataframe.map(self.__helper_convert_string_numeric, dtype=totype)

    def __helper_convert_string_numeric(self, x: str, dtype: str) -> pd.DataFrame:
        """Convert string numeric.

        Args:
            x (str): Before conversion.
            dtype (str): Converted data type.

        Returns:
            pd.DataFrame: After conversion.

        """
        if dtype not in ["float", "int"]:
            err_msg = f"UnSupported dtype: {dtype}"
            raise StructuredError(err_msg)
        try:
            if dtype == "float":
                return float(x)
            return int(x)
        except ValueError:
            err_msg = f"Failed to convert {x} to {dtype}"
            raise StructuredError(err_msg) from None

    def __validation_greek_characters(self, text: str) -> str:
        """Validate greek characters.

        Args:
            text (str): String to be verified.

        Returns:
            str: Post-validated string.

        """
        char_maps = {"TwoThetaTheta": "2Theta-Theta", "2θ/θ": "2Theta-Theta", "2θ": "2Theta"}
        replace_value = char_maps.get(text)
        if replace_value:
            return replace_value
        return text
