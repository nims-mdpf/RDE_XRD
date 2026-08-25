from __future__ import annotations

import re
from collections import defaultdict
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pandas as pd
from rdetoolkit.exceptions import StructuredError
from rdetoolkit.models.rde2types import MetaType, RepeatedMetaType
from rdetoolkit.rde2util import CharDecEncoding

from file_formats.file import BaseFileReader, BaseMetaParser, ExtendMetaType


class FileReader(BaseFileReader):
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

    def read(self, srcpath: Path) -> Generator[tuple[pd.DataFrame, ExtendMetaType]]:
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

    def search_element_with_substring(
        self,
        header_info: ExtendMetaType,
        substring: str,
        *,
        pattern: str = r'"(.*?)"',
    ) -> str:
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

    def __helper_convert_string_numeric(self, x: str, dtype: str) -> float | int:
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


class MetaParser(BaseMetaParser):
    """Parses metadata and saves it to a specified path.

    This class is designed to parse metadata from a dictionary and save it to a specified path using
    a provided Meta object. It can handle both constant and repeated metadata.

    Attributes:
        const_meta_info (MetaType | None): Dictionary to store constant metadata.
        repeated_meta_info (RepeatedMetaType | None): Dictionary to store repeated metadata.

    """

    __mode__ = "ras"

    def __init__(self, *, metadata_def_json_path: Path | None = None, config: dict[str, str | None]):
        super().__init__(metadata_def_json_path=metadata_def_json_path, config=config)
        self.repeated_meta_info: RepeatedMetaType = defaultdict(list)

    def parse(self, data: ExtendMetaType) -> tuple[MetaType, RepeatedMetaType]:
        """Parse and extract constant and repeated metadata from the provided data.

        Args:
            data (ExtendMetaType): The data containing metadata.

        Returns:
            tuple[MetaType, RepeatedMetaType]: A tuple containing two dictionaries - the first one for constant metadata
            and the second one for repeated metadata.

        """
        if isinstance(data, list):
            self.__convert_multi_region_headeritems(data)
        return self.const_meta_info, self.repeated_meta_info

    def __transform_meta(self, meta_string_line: str) -> tuple[str, str]:
        """Transform a meta string into a key-value pair.

        This function takes a meta string in the format '*<key> "<value>"',
        removes the '*', splits the string at ', ', and removes the double
        quotations from the value.

        Args:
            meta_string_line (str): A meta string in the format '*<key> "<value>"'.

        Returns:
            tuple: A tuple containing the key and value as separate strings.

        Examples:
            >>> transform_meta('*sample_meta "1000"')
            ('sample_meta', '1000')

        """
        del_prefix_string = meta_string_line.replace("*", "")
        match = re.match(r'(\S+)\s+"([^"]*)"', del_prefix_string)
        if match:
            key, value = list(match.groups())
            key, value = self.__validate_meta_items(key, value)
            return key, value
        return "", ""

    def __convert_multi_region_headeritems(self, headers: list[Any]) -> dict:
        """Process to merge multiple header information.

        If multiple regions exist and you want to output them as "variable" in metadata.json,
        because it is necessary to convert them to the format of dict[str, list[str]].

        Args:
            headers (list[Any]): list object with one or more header information

        Returns:
            dict: Merged Header Information

        Examples:
            d1 = {"*FILE_OPERATOR" : "administrator", "*FILE_SMAPLE" : "M001"}
            d2 = {"*FILE_OPERATOR" : "admin", "*FILE_SAMPLE" : "M002", "ID": "10"}
            headers = [d1, d2]
            rtn = __multi_region_header(dictHdrs)
            >>> {"*FILE_OPERATOR" : ["administrator", "admin"], "*FILE_SAMPLE" : ["M001", "M002"], "ID": ["10"]}

        """
        for header in headers:
            key, value = self.__transform_meta(header)
            if key:
                self.repeated_meta_info[key].append(value)
        return dict(self.repeated_meta_info)

    def __validate_meta_items(self, meta_key: str, meta_value: str) -> tuple[str, str]:
        """Validate meta items.

        Args:
            meta_key (str): Key.
            meta_value (str): Value.

        Returns:
            tuple: A tuple containing the key and value as separate strings.

        """
        variadation_target_meta_keys = ["MEAS_SCAN_AXIS_X", "MEAS_COND_XG_WAVE_TYPE"]
        if meta_key not in variadation_target_meta_keys:
            return meta_key, meta_value

        _local_meta_key = meta_key
        _local_meta_value = meta_value
        if _local_meta_key == "MEAS_COND_XG_WAVE_TYPE":
            if "a" in _local_meta_value:
                _local_meta_value = _local_meta_value.replace("a", "_alpha")
            if "b" in _local_meta_value:
                _local_meta_value = _local_meta_value.replace("b", "_beta")
        elif _local_meta_key == "MEAS_SCAN_AXIS_X":
            if _local_meta_value in ["TwoThetaTheta", "2θ/θ"]:
                _local_meta_value = "2Theta-Theta"
        return _local_meta_key, _local_meta_value
